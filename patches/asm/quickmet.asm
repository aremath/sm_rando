lorom

; From https://patrickjohnston.org/ASM/ROM%20data/Super%20Metroid/quickmet.asm

; Change these:
!roomId       = $AC5A
!samusX_start = $0070
!samusY_start = $0078

!decompressionSource    = $47
!decompressionDest      = $4C
!tempDoorEntry          = $02A0
!doorPointer            = $078D
!specialGfxBitflag      = $07B3
!gameState              = $0998
!doorTransitionFunction = $099C
!samusX                 = $0AF6
!samusY                 = $0AFA
!creTileTable           = $7EA000


; Skip area select screen?
{
org $819154
NOP : NOP
}


; Combine PPU register initialisation with VRAM initialisation (saves a call I guess...)
{
org $8282C3
BRA +

org $8282E3
+

; Change the RTS to an RTL so it can be called from bank $8B
org $828366
RTL
}


; Gamestate 01 - opening. The main code
{
org $8B9A22
REP #$30
PHB
PHK : PLB
SEI

; Set game state to door transition
LDA #$000B : STA !gameState

; Skip waiting for sounds to finish and screen to fade out
LDA #$E2F7 : STA !doorTransitionFunction

; Set up a door entry in RAM
LDA #!tempDoorEntry : STA !doorPointer
LDX #$000A

-
LDA doorEntry,x : STA !tempDoorEntry,x
DEX : DEX
BPL -

; Initialise PPU registers and VRAM
JSL $8281DD

; Initialise Samus
JSL $91E00D

; Load from SRAM (slot 0)
LDA #$0000 : JSL $818085

; Decompress CRE tiles to VRAM $2800
LDA #$0080 : STA $2115
LDA #$B900 : STA !decompressionSource+1
LDA #$8000 : STA !decompressionSource
LDA #$5000 : STA !decompressionDest
LSR A : STA $2116
JSL $80B271

; Decompress CRE tile table to $7E:A000
LDA #$B900 : STA !decompressionSource+1
LDA #$A09D : STA !decompressionSource
JSL $80B0FF : dl !creTileTable

; Set Samus' position
LDA #!samusX_start : STA !samusX
LDA #!samusY_start : STA !samusY

; Load timer until Samus can move?
LDA #$0167 : STA $0DEC

; Enable screen (full brightness)
SEP #$20
LDA #$0F : STA $51

; Load HUD
JSL $809A79

; Load special GFX bitflag
LDX doorEntry : LDA $8F0008,x : STA !specialGfxBitflag

JSL $8483AD ; Enable PLMs
JSL $868000 ; Enable enemy projectiles
JSL $878000 ; Enable animated tiles objects
CLI
REP #$30
PLB

; Display the viewable part of the room
JSL $80A176

; Enable atmospheric effects?
LDA #$8000 : STA $1E79
RTL

; Padding I guess
dl $000000, $000000

doorEntry:
dw !roomId  ; Destination room
db $00      ; Flags
db $00      ; Direction
db $00      ; Doorcap X
db $00      ; Doorcap Y
db $00      ; Destination X
db $00      ; Destination Y
dw $03F0    ; Distance from door
dw $0000    ; Door ASM
}
