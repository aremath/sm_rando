; Keeps just the teleportation part of total's practice hack: https://github.com/tewtal/sm_practice_hack
; Thanks to total for helping!
lorom

!ram_ctrl = $8B
!ram_ctrl_filtered = $8F
!INPUT = #$3000 ; Start + Select

org $828963
    JSL hijack : BCS end_of_normal_gameplay

org $82896E
    end_of_normal_gameplay:

; Free space in $82
;org $82F800

org $85A000

hijack:
    ;PHB
    ;PHK : PLB

    ; Check for the input being pressed (newly)
    LDA !ram_ctrl : AND !INPUT : CMP !INPUT : BNE no
    AND !ram_ctrl_filtered : BEQ no
    print pc, " teleport"
    JSR teleport
    
    no:
	;PHP
    LDA $0998 : AND #$00FF
    ;PLP
    ;PLB
    RTL

teleport:
    ; Check if the escape sequence is active -- if it's active, don't allow teleportation
    ; This check is only enabled in the noescape version.
    LDA $7E0943
    CMP #$0000
    BNE refill
    LDA #$0000
    ; Set the area index to 0 (Crateria)
    STA $7E079F
    ; Set the save station index to 0 (Ship)
    STA $7E078B
    ; Set the game state to 6 (Load a save)
    LDA #$0006
    STA $7E0998
    JSR stop_all_sounds
    RTS

refill:
	;refill missiles
	LDA $7E09C8
	STA $7E09C6
	;refill supers
	LDA $7E09CC
	STA $7E09CA
	;refill PBs
	LDA $7E09D0
	STA $7E09CE
	RTS

stop_all_sounds:
    ; If $05F5 is non-zero, the game won't clear the sounds
    LDA $05F5 : PHA
    LDA #$0000 : STA $05F5
    JSL $82BE17
    PLA : STA $05F5

    ; Makes the game check Samus' health again, to see if we need annoying sound
    LDA #$0000 : STA $0A6A
    RTS