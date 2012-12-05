arm-elf-as -mcpu=arm7tdmi patch.s -o patch.o
arm-elf-ld -Ttext 0x8089e0 -o patch.bin patch.o

