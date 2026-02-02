#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/smp.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Grady Kestler");
MODULE_DESCRIPTION("This module enables users to access performance counter on both CPUs");

static void enable_counters(void* data){
  asm ("MCR p15, 0, %0, c9, c14, 0\n\t" :: "r"(1));
  // disable counter overflow interrupts
  asm ("MCR p15, 0, %0, c9, c14, 2\n\t" :: "r"(0x8000000f));
}

static void disable_counters(void* data){
  // disable user-mode access to the performance counter
  asm ("MCR p15, 0, %0, c9, c14, 0\n\t" :: "r"(0));
}

static int __init init(void){
  on_each_cpu(enable_counters, NULL, 1);
  printk(KERN_INFO "CPU counter enabled on both CPUs.\n");
  return 0;
}

static void __exit clean(void){
  on_each_cpu(disable_counters, NULL, 1);
  printk(KERN_INFO "CPU counter disabled on both CPUs.\n");
}

module_init(init);
module_exit(clean);
