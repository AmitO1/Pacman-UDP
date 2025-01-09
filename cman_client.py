import socket
import select
import struct
import argparse
import cman_game_map
import cman_game
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

def update_map(game_map: str, c_coords: tuple, s_coords: tuple, collected:str):
    game_map = game_map.replace('C', 'F')
    game_map = game_map.replace('S', 'F')
    list_map = []
    row = []
    count = 0
    point_dict = cman_game.Game('map.txt').get_points() #used only for points location constant throught the game
    for char in game_map:
        if char == '\n':
            row.append(char)
            list_map.append(row)
            row = []
        else:
            row.append(char)
            
    list_map.append(row)
    
    list_map[c_coords[0]][c_coords[1]] = 'C'
    list_map[s_coords[0]][s_coords[1]] = 'S'
    game_map = ''
    for i, row in enumerate(list_map):
        for j, col in enumerate(row):
            if (i,j) in point_dict:
                if col != 'S' and col != 'C':
                    col = 'P' if collected[count] == '1' else 'F' 
                    
                count+=1
                
            game_map += col    
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
    elif opcode == OPCODE_GAME_END:
        unpacked_data = struct.unpack('!B B B',message)
        winner = unpacked_data[0]
        s_score = unpacked_data[1]
        c_score = unpacked_data[2]
        
        return {
            'opcode' : opcode,
            'winner' : winner,
            's_score' : s_score,
            'c_score' : c_score           
        }
        
    else:
        # Handle other opcodes here as needed
        print(f"Unknown opcode: {opcode}")
        return None

is_game_over = False 
logged_in = False
is_playable = False
map_g = cman_game_map.read_map('map.txt')
final_message = ''

# Create a UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

client_socket.setblocking(False)

key_list = []

#TODO - beforte sumbitting change function to get_pressed_keys
try:
    while True and not is_game_over:
        # Get input from the user
        readable, writable, _ = select.select([client_socket], [client_socket], [])
        if client_socket in writable:
                
            if logged_in == False:
                message = struct.pack('BB', OPCODE_JOIN, int(ROLE))
                client_socket.sendto(message, (SERVER_ADDRESS, PORT))
                logged_in = True
                
            elif is_playable:
                print(cman_game_map.transform_map(map_g))
                if ROLE != 0:
                    key_list = input("Enter keys movement:")
                    key = get_key(key_list)
                    if key == 'q':
                        message = struct.pack('B',OPCODE_QUIT)
                        client_socket.sendto(message, (SERVER_ADDRESS, PORT))
                        is_game_over = True
                        client_socket.close()
                        final_message = "Quitted from the game"
                        
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
                else:
                    print(cman_game_map.transform_map(map_g)) 
                            
        if client_socket in readable and not is_game_over:
            data, server = client_socket.recvfrom(1024)  
            unpacked_data = unpack_message(data)
            
            #in case if any error server close connection and client disconnect
            if unpacked_data['opcode'] == OPCODE_ERROR:
                error_msg = unpacked_data['error_msg']
                
                if error_msg == ERROR_CMAN or error_msg == ERROR_GHOST:
                    final_message = 'Cman already taken closing connection...' if error_msg == ERROR_CMAN else 'Ghost already taken closing connection...' 
                    
                is_game_over = True
                client_socket.close()
                
            elif unpacked_data['opcode'] == OPCODE_GAME_STATE_UPDATE:          
                map_g = update_map(map_g,unpacked_data['c_coords'],unpacked_data['s_coords'],unpacked_data['collected'])
                if unpacked_data['freeze'] == 1:
                    is_playable= True
                    
            elif unpacked_data['opcode'] == OPCODE_GAME_END:
                if unpacked_data['winner'] == 1:
                    final_message = 'Winner is Cman, Cman scored ' + str(unpacked_data['c_score']) + ' points and got caught ' + str(unpacked_data['s_score']) + ' times!'
                else:
                    final_message = 'Winner is Ghost, Cman was caught 3 times and scored only ' + str(unpacked_data['c_score']) + 'points!'
                is_game_over = True 
                              
        cman_utils.clear_print()
            
        
except KeyboardInterrupt:
    print("\nClient interrupted. Exiting.")
finally:
    # Close the socket
    print(final_message)
    client_socket.close()



"""
            elif logged_in and not is_playable:
                    key_list = input("Enter keys movement:")
                    key = get_key(key_list)
                    if key == 'q':
                        message = struct.pack('B',OPCODE_QUIT)
                        client_socket.sendto(message, (SERVER_ADDRESS, PORT))
                        is_game_over = True
                        client_socket.close()
                        final_message = "Quitted from the game"
"""