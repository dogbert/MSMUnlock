@
@ Copyright 2009:  dogbert <dogber1@gmail.com>
@
@ This program is free software; you can redistribute it and/or modify
@ it under the terms of the GNU General Public License as published by
@ the Free Software Foundation; either version 2 of the License, or
@ (at your option) any later version.
@
@ This program is distributed in the hope that it will be useful,
@ but WITHOUT ANY WARRANTY; without even the implied warranty of
@ MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
@ GNU General Public License for more details.
@
@ You should have received a copy of the GNU General Public License
@ along with this program; if not, write to the Free Software
@ Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
@

.align 4
.thumb_func

	push	{r1-r7,lr}
@ memclr(output paket)
	ldr	r0, =(offsetPkt)
	mov	r1, #(1+9+2+1)
	bl	memclr

	mov	r1, #6
	str	r1, [r0]

	ldr	r3,=0x1E00000 @ start address
	mov	r4, #10       @ timeout
	ldr	r5,=NANDbase1
	ldr	r6,=NANDbase2
	ldr	r7,=NANDbase3
start_loop:
	str	r3, [r6]

do_read:
	sub	r4, r4, #1
	mov	r0, r4
	cmp	r4, #0
	beq	next_iteration

	mov	r0, #1
	str	r0, [r7,#12] 
	str	r0, [r6,#4] 
	bl	wait
	ldr	r0, [r5]
	cmp	r0, #0
	beq	do_read
	ldr	r1, [r5,#16]
	cmp	r1, #0
	bne	do_read
	lsl	r1, r0, #0x10
	lsr	r2, r0, #0x10
	lsl	r2, r2, #0x10
	cmp	r2, r1
	beq	do_read

	ldr	r1, [r5,#4]
	ldr	r2, [r5,#8]
	eor	r0, r2
	ldr	r2, [r5,#12]
	eor	r1, r2
	bl	isNumber
next_iteration:
	add	r3, #0xFF @ try higher address
	add	r3, #0xFF
	add	r3, #2
	lsr	r2, r3,#0x18
	cmp	r2, #0x2
	beq	error
	mov	r4, #10
	cmp	r0, #0
	beq	start_loop

	ldr	r2, =(offsetPkt+1)
	str	r1, [r2,#4]
	ldr	r1, [r2]
	str	r0, [r2]
	cmp	r1, #0
	beq	do_read

	b	exit
error:
	ldr	r2, =error_str
	ldr	r0, [r2]
	ldr	r1, [r2,#4]
	ldr	r2, =(offsetPkt+1)
	str	r0, [r2]
	str	r1, [r2,#4]
exit:
	mov	r3, #9
	ldr	r1, =offsetPktLen
	str	r3, [r1]
	ldr	r4, =preparePkt
	bl	call_handler
	ldr	r4, =sendPkt
	bl	call_handler
	mov	r0, #0
	pop	{r1-r7,pc}

@ wait a couple of cycles
wait:
	push	{r0}
	mov	r0, #0xff
	add	r0, r0, r0
	lsl	r0, #4 
wait_loop:
	sub	r0, r0, #1
	cmp	r0, #0
	bne	wait_loop
	pop	{r0}
	bx	lr

isNumber:
	push	{r2-r4}
	mov	r3, r0
	mov	r4,#1
check:
	mov	r2, #0xff
	and	r2, r3
	cmp	r2, #0x30
	bcc	not_a_number
	cmp	r2, #0x39
	bhi	not_a_number
	lsr	r3, #8
	cmp	r3, #0
	bne	check
	cmp	r4, #0
	beq	number
	mov	r4, #0
	mov	r3, r1
	b	check	
not_a_number:
	mov	r0, #0
number:
	pop	{r2-r4}
	bx	lr

@ r0 - offset, r1 - length
memclr:
	push	{r0-r3}
	mov	r3, #0
memclr_loop:
	str	r3, [r0]
	add	r0, r0, #1
	sub	r1, r1, #1
	cmp	r1, #0
	bne	memclr_loop
	pop	{r0-r3}
	bx	lr

call_handler:
	mov	pc, r4

@ basic definitions
.equ NANDbase1,0x60000000
.equ NANDbase2,0x60000300
.equ NANDbase3,0x80005400
.equ offsetPkt,0x827160
.equ offsetPktLen,0x80D6F8
@ functions
.equ preparePkt,0x800710
.equ sendPkt,0x8052A8
@strings
error_str:
.ascii	"error..."
