; Press start+select to reset to the ship
; Author: Aremath
; Based on total's sm practice hack: github.com/tewtal/sm_practice_hack
; TODO: Mother Brain fight disables this feature

lorom

!SHIP_REGION = #$00
!SHIP_INDEX = #$00

!MENU_BANK_START = $DFEA00 ; Where to put the code
;!MENU_BANK_START = $B80000 ; Where to put the code
!MENU_INPUT = #$3000 ; Select + Start in the input bitflag
!MENU_CONTROLLER = $7E008B ; Where to read inputs from
!MENU_CONTROLLER_NEW = $7E008F
!MENU_CONTROLLER_PREV = $7E0097

; Hijack init code
;org $808449
;    JSL todo_init : NOP

; Hijack end of NMI
org $8095F7
    JSL nmi_init : NOP

org !MENU_BANK_START

nmi_init:
    REP #$30 ; 16-bit width registers
    PHA ; Save accumulator from during NMI

    ; Check if Start + Select pressed
    LDA !MENU_CONTROLLER
    CMP !MENU_INPUT
    BNE nmi_done

    ; Start + Select were pressed, so teleport!
    JSR teleport_ship

    ; Reset inputs to prevent the game from pausing
    LDA #$0000
    STA !MENU_CONTROLLER
    STA !MENU_CONTROLLER_NEW
    STA !MENU_CONTROLLER_PREV

    ; We're done regardless
    JMP nmi_done

nmi_done:
    PLA ; Reload accumulator for re-entering NMI
    INC $7E05B8 ; Increment NMI counter
    RTL

teleport_ship:  
    ; Set the NMI flag
    ;SEP #$20
    ;LDA #$01
    ;STA $05B4
    ;REP #$30

    ; Load the ship region into memory
    ; where the game expects the current save region
    LDA !SHIP_REGION
    STA $7E079F
    ; Load the index of the ship save station into memory
    LDA !SHIP_INDEX
    STA $7E078B
    ; Set the "loading a save" value for game state
    LDA #$0006
    STA $7E0998
    
    ; Handle the HUD ?
    ;JSL $809A79
    ;JSL $809B44

    RTS

