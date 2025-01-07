import socket
import select
import struct
import argparse
import cman_game_map
import cman_utils

# Setup argparse to handle command-line arguments
parser = argparse.ArgumentParser(description="Rescieve argument from user")
parser.add_argument('role', type=int, choices=[0, 1, 2], help="Role to send (0, 1, or 2)")
parser.add_argument('addr', type=str, help="Server address (IP or hostname)")
parser.add_argument('-p', '--port', type=int, default=1337, help="Port number (default: 1337)")

# Parse the arguments
args = parser.parse_args()

# Get the values from the parsed arguments
role = args.role
addr = args.addr
port = args.port

SERVER_ADDRESS = addr 
PORT = port 
ROLE = role
# Client to Server
OPCODE_JOIN = 0x00
OPCODE_PLAYER_MOVEMENT = 0x01
OPCODE_QUIT = 0x0F

# Server to Client
OPCODE_GAME_STATE_UPDATE = 0x80
OPCODE_GAME_END = 0x8F
OPCODE_ERROR = 0xFF          

ERROR_ILLEGAL = 'ERROR1'
ERROR_CMAN = 'ERROR2'
ERROR_GHOST = 'ERROR3'

def get_key(key_list):
    target_char = {'a','s','d','w','q'}
    for key in key_list:
        if key in target_char:
            return key
    return None

def update_map(game_map: str, c_coords: tuple, s_coords: tuple):
    game_map = game_map.replace('C', ' ')
    game_map = game_map.replace('S', ' ')
    list_map = []
    row = []
    for char in game_map:
        if char == '\n':
            list_map.append(row)
            row = []
        else:
            row.append(char)
    list_map[c_coords[0]][c_coords[1]] = 'C'
    list_map[s_coords[0]][s_coords[1]] = 'S'
    game_map = ''
    for row in list_map:
        for col in row:
            game_map += col
        game_map+= '\n'
        
    return game_map

def unpack_message(data):
    # Extract the opcode
    opcode = data[0]
    message = data[1:]
    
    if b'ERROR' in message:
        return{
            'opcode': opcode,
            'error_msg': message.decode()
        }
        
    elif opcode == OPCODE_GAME_STATE_UPDATE:
        # Unpack for opcode 0x80
        unpacked_data = struct.unpack('!B B B B B B 40s', message)
        freeze = unpacked_data[0]
        c_coords = (unpacked_data[1], unpacked_data[2])
        print(f"c_coords: {c_coords}")
        s_coords = (unpacked_data[3], unpacked_data[4])
        attempts = unpacked_data[5]
        collected = unpacked_data[6].decode('utf-8')
        # Return the unpacked values
        return {
            'opcode': opcode,
            'freeze': freeze,
            'c_coords': c_coords,
            's_coords': s_coords,
            'attempts': attempts,
            'collected': collected
        }
    else:
        # Handle other opcodes here as needed
        print(f"Unknown opcode: {opcode}")
        return None


logged_in = False
map_g = cman_game_map.read_map('map.txt')

# Create a UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

client_socket.setblocking(False)

key_list = []


try:
    while True:
        print(cman_game_map.transform_map(map_g))
        # Get input from the user
        readable, writable, _ = select.select([client_socket], [client_socket], [])
        if client_socket in writable:
                
            if logged_in == False:
                message = struct.pack('BB', OPCODE_JOIN, int(role))
                client_socket.sendto(message, (SERVER_ADDRESS, PORT))
                logged_in = True
            else:
                if ROLE != 0:
                    key_list = input("Enter keys movement:")
                    key = get_key(key_list)
                    print(key)
                    if key == 'q':
                        message = struct.pack('B',OPCODE_QUIT)
                        client_socket.sendto(message, (SERVER_ADDRESS, PORT))
                    elif key == 'w':
                        message = struct.pack('BB',OPCODE_PLAYER_MOVEMENT,int(0))
                        client_socket.sendto(message, (SERVER_ADDRESS, PORT))   
                    elif key == 'a':
                        message = struct.pack('BB',OPCODE_PLAYER_MOVEMENT,int(1)) 
                        client_socket.sendto(message, (SERVER_ADDRESS, PORT))
                    elif key == 's':
                        message = struct.pack('BB',OPCODE_PLAYER_MOVEMENT,int(2)) 
                        client_socket.sendto(message, (SERVER_ADDRESS, PORT))
                    elif key == 'd':
                        message = struct.pack('BB',OPCODE_PLAYER_MOVEMENT,int(3))
                        client_socket.sendto(message, (SERVER_ADDRESS, PORT)) 
                            
        if client_socket in readable:
            data, server = client_socket.recvfrom(1024)  
            unpacked_data = unpack_message(data)
            
            #TODO change implementation
            if unpacked_data['opcode'] == OPCODE_ERROR:
                client_socket.close()
            elif unpacked_data['opcode'] == OPCODE_GAME_STATE_UPDATE:          
                map_g = update_map(map_g,unpacked_data['c_coords'],unpacked_data['s_coords'])
            
        cman_utils.clear_print()
        
except KeyboardInterrupt:
    print("\nClient interrupted. Exiting.")
finally:
    # Close the socket
    client_socket.close()




        