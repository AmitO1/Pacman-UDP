import socket
import select
import cman_game
import cman_game_map
import argparse
import struct

GAMEMAP = cman_game_map.read_map('map.txt')
HOST = ''
PORT = 1337
is_cman = False
is_ghost = False

# Client to Server
OPCODE_JOIN = 0x00
OPCODE_PLAYER_MOVEMENT = 0x01
OPCODE_QUIT = 0x0F

# Server to Client
OPCODE_GAME_STATE_UPDATE = 0x80
OPCODE_GAME_END = 0x8F
OPCODE_ERROR = 0xFF

UP = 0
LEFT = 1
DOWN = 2
RIGHT = 3
CMAN_JOIN = 'C'
GHOST_JOIN = 'G'
WACTCHER_JOIN = 'W'
ERROR_ILLEGAL = 'ERROR1'
ERROR_CMAN = 'ERROR2'
ERROR_GHOST = 'ERROR3'
ERROR_MOVEMENT = 'ERROR4'

def dict_to_binary_string(coord_dict):
    # Create the binary string from the values in the dictionary
    binary_string = ''.join(str(coord_dict[coord]) for coord in coord_dict)

    return binary_string

def handle_login(attributes):
    global is_cman,is_ghost
    if len(attributes) > 1:
        return ERROR_ILLEGAL
    if (attributes[0] == 1):
        if not is_cman:
            is_cman = True
            return CMAN_JOIN
        else:
            return ERROR_CMAN
    if (attributes[0] == 2):
        if not is_ghost:
            is_ghost = True
            return GHOST_JOIN
        else:
            return ERROR_GHOST
    if(attributes[0] == 0):
        return WACTCHER_JOIN
    
    return ERROR_ILLEGAL #impossible to read due to argparse + error = disconned no need to handle


        
def read_message(opcode, attributes):
    if opcode == OPCODE_JOIN:
        return handle_login(attributes)
    if opcode == OPCODE_PLAYER_MOVEMENT:
        return attributes[0]
    if opcode == OPCODE_QUIT:
        return 'quit'
    
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))  


server_socket.setblocking(False)

# List of sockets to monitor
read_sockets = [server_socket]
error_queue = {}  # Keep track if a client need to recieve an error
cman_addr = ''
ghost_addr = ''
clients = set()
game = cman_game.Game('map.txt')
freeze_cman = 0
freeze_ghost = 0
clients_to_remove = set()

try:
    while True:   
            
        for client in clients_to_remove:
            print(f"test: {client}")
            clients.remove(client)
        clients_to_remove = set()
        
        readable, _, _ = select.select(read_sockets, [], [],1) #TODO lower delay - this high for mac
        # Handle readable sockets
        for s in readable:
            if s is server_socket:
                # Receive data
                data, addr = server_socket.recvfrom(1024)
                
                #add all client to send update message each loop
                clients.add(addr)
                
                opcode = data[0]
                attributes = data[1:]
                action = read_message(opcode,attributes)
                
                print(f"action: {action}")
                
                if action == CMAN_JOIN:
                    print("Cman joined!")
                    cman_addr = addr
                    
                elif action == GHOST_JOIN:
                    print("Ghost joined!")
                    ghost_addr = addr
                elif action == WACTCHER_JOIN:
                    print("A watcher joined!")
                    
                elif action == UP or action == DOWN or action == LEFT or action == RIGHT:
                    print(f"Moving {'up' if action == UP else 'down' if action == DOWN else 'left' if action == LEFT else 'right'} ")
                    
                    if game.state == cman_game.State.START and addr == cman_addr:
                        game.state = cman_game.State.PLAY
                        freeze_cman = 1
                        game.apply_move(0,action)
                    
                    if game.state == cman_game.State.PLAY:
                        freeze_ghost = 1
                        freeze_cman = 1
                        if addr == ghost_addr:
                            print("ghost moving from here")
                            game.apply_move(1,action)
                        if addr == cman_addr:
                            print("cman moving from here")
                            game.apply_move(0,action)
                            
                    if addr == ghost_addr:
                        print(f"game state {game.state}")
                        
                elif action == 'quit':#TODO - handle winner 
                    print(f"{'cman' if addr == cman_addr else 'ghost' if addr == ghost_addr else 'watcher'} is quitting")
                    if addr == cman_addr:
                        is_cman = False
                        cman_addr = ''
                        clients.remove(addr)
                    if addr == ghost_addr:
                        is_ghost = False
                        ghost_addr = ''
                        clients.remove(addr)
                    
                elif 'ERROR' in action:
                    print("An ERROR has occured")
                    error_message_bytes = action.encode('utf-8')
                    response = struct.pack('!B 6s', OPCODE_ERROR,error_message_bytes) 
                    error_queue[addr] = response
                    
        
        coords = game.get_current_players_coords() 
        c_coords = coords[0]
        s_coords = coords[1] 
        attemptes = game.get_game_progress()[0]
        collected = dict_to_binary_string(game.get_points())  
            
        for client in clients:
            
            #check if both connected and game state isnt play / start already to update game status
            if is_ghost and is_cman and game.state == cman_game.State.WAIT :
                
                game.state = cman_game.State.START
                
                if client == cman_addr:
                    freeze_cman = 1
                    
            if client in error_queue:
                print(f"Send error to client in address: {client}")
                server_socket.sendto(error_queue[client],client)
                del error_queue[client]
                clients_to_remove.add(client)
                
            elif client == cman_addr:
                print(f"sending cman to c_coords: {c_coords}")
                packed_message = struct.pack(
                '!B B B B B B B 40s',
                OPCODE_GAME_STATE_UPDATE,  
                freeze_cman,  
                c_coords[0], c_coords[1],  
                s_coords[0], s_coords[1],  
                attemptes,  
                collected.encode('utf-8')  
                )
                server_socket.sendto(packed_message,client)
            elif client == ghost_addr:
                print(f"sending ghost to s_coords: {s_coords}")
                packed_message = struct.pack(
                '!B B B B B B B 40s',
                OPCODE_GAME_STATE_UPDATE,  
                freeze_ghost,  
                c_coords[0], c_coords[1],  
                s_coords[0], s_coords[1],  
                attemptes,  
                collected.encode('utf-8')  
                )
                server_socket.sendto(packed_message,client)
            else:
                packed_message = struct.pack(
                '!B B B B B B B 40s',
                OPCODE_GAME_STATE_UPDATE,  
                0,  
                c_coords[0], c_coords[1],  
                s_coords[0], s_coords[1],  
                attemptes,  
                collected.encode('utf-8')  
                )
                server_socket.sendto(packed_message,client)


except KeyboardInterrupt:
    print("Server shutting down...")
finally:
    server_socket.close()
