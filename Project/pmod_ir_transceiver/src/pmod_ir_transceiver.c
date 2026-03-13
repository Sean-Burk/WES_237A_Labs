#include "circular_buffer.h"
#include "xio_switch.h"
#include "timer.h"
#include "gpio.h"

// Mailbox commands
#define CONFIG_IOP_SWITCH       0x1
#define GENERATE                0x3
#define STOP                    0x5
#define WRITE                   0x7
#define READ                    0x9


// Temp defines
#define DATA_RATE_HZ 10
#define IR_PULSE_RATE 36*100 // this is equivelent to approx 38KHz
#define PULSE_WIDTH_US 200
#define PULSE_SPACE_US 300

/*
 * TIMING_INTERVAL = (TLRx + 2) * AXI_CLOCK_PERIOD
 * PWM_PERIOD = (TLR0 + 2) * AXI_CLOCK_PERIOD
 * PWM_HIGH_TIME = (TLR1 + 2) * AXI_CLOCK_PERIOD
 */

/*
 * Parameters passed in MAILBOX_WRITE_CMD
 * bits 31:16 => period in us
 * bits 15:8 is not used
 * bits 7:1 => duty cycle in %, valid range is 1 to 99
 */

/************************** Function Prototypes ******************************/
static timer device;
gpio receiver_gpio;

void blocking_wait_ms(u32 ms){
    // Since there is only one timer per MicroBlaze by default 
    // and the PWM takes up both channels on the timer
    // we have to do this dumb wait
    for (u32 i = 0; i < ms * 5000; i++) {
        __asm__("nop"); 
    }
}

void blocking_wait_us(u32 us){
    // Since there is only one timer per MicroBlaze by default 
    // and the PWM takes up both channels on the timer
    // we have to do this dumb wait
    for (u32 i = 0; i < us * 5; i++) {
        __asm__("nop"); 
    }
}



void write_ir(timer dev, u8 buffer[64], u32 len){
    for(int i=0;i<len;i++){
        for(int j=0;j<8;j++){
            timer_pwm_generate(dev, IR_PULSE_RATE, IR_PULSE_RATE*50/100);
            blocking_wait_us(PULSE_WIDTH_US);
            timer_pwm_stop(dev);
            blocking_wait_us(PULSE_SPACE_US*(1+((buffer[i]>>(7-j))&0x01)));
        }
    }
    // extra pulse on the end because we are using pulse distance encoding
    timer_pwm_generate(dev, IR_PULSE_RATE, IR_PULSE_RATE*50/100);
    blocking_wait_us(PULSE_WIDTH_US);
    timer_pwm_stop(dev);
}

int read_ir(u8 buffer[64], u32 read_len, u32* err){
    // read until we receive read_len bytes or there is a pulse space
    // that isn't +/- PULSE_SPACE_US/2 from where it's supposed to be
    u8 old, new, rounded;
    u32 pulse_space_count = 0;
    u32 bit_pos = 0;
    // 0 is signal and we wait until signal before trying to decode
    old = 0; 
    while(gpio_read(receiver_gpio)){}
    while(1){
        blocking_wait_us(10);
        new = gpio_read(receiver_gpio);
        if(new) // we incriment by a few extra usec to make up for gpio reat time
            pulse_space_count+=12;
        if(old<new){
            // Falling edge
            pulse_space_count=0;
        }
        else if(old>new){
            // Rising edge
            rounded = (pulse_space_count+PULSE_SPACE_US/2)/PULSE_SPACE_US;
            if(rounded==1){
                // *err |= 2;
                // 0 bit
                buffer[bit_pos/8] &= ~(1<<(7-(bit_pos%8)));
                bit_pos++;
            }
            else if(rounded==2){
                *err += 1;
                // 1 bit
                buffer[bit_pos/8] |= (1<<(7-(bit_pos%8)));
                bit_pos++;
            }
            else{
                // invalid pulse space data is probably corrupted
                // *err |= 1;
                break;
            }
        }
        if(pulse_space_count>PULSE_SPACE_US*2+PULSE_SPACE_US/2 ||
          bit_pos/8>=read_len){
            // too long since last pulse or done with read
            break;
        }
        old=new;
    }
    return bit_pos/8;
}

int main(void) {
    u32 cmd;
    u32 Timer1Value, Timer2Value;
    u32 pwm_pin, gpio_pin;
    u8 buffer[64];
    u32 arg1, arg2;
    u32 error=0;

    /*
     * Configuring Pmod IO switch
     * bit-0 is controlled by the pwm
     */
    device = timer_open_device(0);
    init_io_switch();

    while(1){
        while(MAILBOX_CMD_ADDR==0);
        cmd = MAILBOX_CMD_ADDR;
        
        switch(cmd){
            case CONFIG_IOP_SWITCH:
                // read new pin configuration
                pwm_pin = MAILBOX_DATA(0);
                gpio_pin = MAILBOX_DATA(1);
                receiver_gpio = gpio_open(gpio_pin);
                gpio_set_direction(receiver_gpio,  GPIO_IN);
                set_pin(pwm_pin, PWM0);

                MAILBOX_CMD_ADDR = 0x0;
                break;
                  
            case GENERATE:
                Timer1Value = (MAILBOX_DATA(0) & 0x0ffff) *100;
                Timer2Value = (MAILBOX_DATA(1) & 0x07f)*Timer1Value/100;
                timer_pwm_generate(device, Timer1Value, Timer2Value);
                MAILBOX_CMD_ADDR = 0x0;
                break;
                
            case STOP:
                timer_pwm_stop(device);
                MAILBOX_CMD_ADDR = 0x0;
                break;
            case WRITE:
                arg1 = (MAILBOX_DATA(0) & 0x7F); // write len
                for(int i=0;i<arg1;i+=4){
                    u32 word = MAILBOX_DATA(1 + i / 4);
                    for (int j = 0; j < 4 && (i + j) < arg1; j++) {
                        buffer[i+j] = (u8)((word >> ((3 - j) * 8))&0xFF);
                    }
                }
                write_ir(device, buffer, arg1);
                MAILBOX_CMD_ADDR = 0x0;
                break;
            case READ:
                arg1 = (MAILBOX_DATA(0)); // read_len
                error= 0;
                arg2 = read_ir(buffer, arg1, &error); // read
                MAILBOX_DATA(0) = arg2; // send back read lenth
                MAILBOX_DATA(1) = error;
                for(int i=0;i<(arg2+3)/4;i++){ // clear mailbox
                    MAILBOX_DATA(2+i) = 0;
                }
                for(int i=0;i<arg2;i+=4){ // write data to mailbox
                    u32 word = 0;
                    for (int j = 0; j < 4 && (i + j) < arg2; j++) {
                        word |= (u32)buffer[i + j] << ((3 - j) * 8);
                    }
                    MAILBOX_DATA(2 + i / 4) = word;
                }
                MAILBOX_CMD_ADDR = 0x0;
                break;
            default:
                MAILBOX_CMD_ADDR = 0x0;
                break;
        }
    }
    return 0;
}
