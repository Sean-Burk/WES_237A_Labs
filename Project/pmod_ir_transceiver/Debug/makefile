# Copyright (C) 2022 Xilinx, Inc
# SPDX-License-Identifier: BSD-3-Clause

################################################################################
# Automatically-generated file. Do not edit!
################################################################################

-include ../makefile.init

RM := rm -rf

# All of the sources participating in the build are defined here
-include sources.mk
-include src/subdir.mk
-include subdir.mk
-include objects.mk

ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(S_UPPER_DEPS)),)
-include $(S_UPPER_DEPS)
endif
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS)
endif
endif

-include ../makefile.defs

# Add inputs and outputs from these tool invocations to the build variables 
ELFSIZE += \
pmod_ir_transceiver.elf.size \


# All Target
all: pmod_ir_transceiver.elf secondary-outputs

# Tool invocations
pmod_ir_transceiver.elf: $(OBJS) ../src/lscript.ld $(USER_OBJS)
	@echo 'Building target: $@'
	@echo 'Invoking: MicroBlaze gcc linker'
	mb-gcc -Wl,-gc-sections -Wl,-T -Wl,../src/lscript.ld -L/usr/local/share/pynq-venv/lib/python3.10/site-packages/pynq/lib/pmod/bsp_iop_pmod/iop_pmoda_mb/lib -mlittle-endian -mcpu=v11.0 -mxl-soft-mul -Wl,--no-relax -o "pmod_ir_transceiver.elf" $(OBJS) $(USER_OBJS) $(LIBS)
	@echo 'Finished building target: $@'
	@echo ' '

pmod_ir_transceiver.elf.size: pmod_ir_transceiver.elf
	@echo 'Invoking: MicroBlaze Print Size'
	mb-size pmod_ir_transceiver.elf  |tee "pmod_ir_transceiver.elf.size"
	@echo 'Finished building: $@'
	@echo ' '

pmod_ir_transceiver.bin: pmod_ir_transceiver.elf
	@echo 'Invoking: MicroBlaze Bin Gen'
	mb-objcopy -O binary pmod_ir_transceiver.elf pmod_ir_transceiver.bin
	@echo 'Finished building: $@'
	@echo ' '

# Other Targets
clean:
	-$(RM) $(EXECUTABLES)$(OBJS)$(S_UPPER_DEPS)$(C_DEPS)$(ELFSIZE) pmod_ir_transceiver.elf pmod_ir_transceiver.bin
	-@echo ' '

secondary-outputs: $(ELFSIZE) pmod_ir_transceiver.bin

.PHONY: all clean dependents
.SECONDARY:

-include ../makefile.targets
