import re

isTEST = True 

class BD:
    def __init__( self ) -> BD:
        pass

if __name__ == "__main__":
    bd = BD()
    with open( "prog.bd", 'r' ) as file:
        bd.execution( file.read().split( '\n' ) )

    with open( "prog.bf", 'w' ) as file:
        file.write( bd.code.code )

    if isTEST == True:
        print(bd.memory)