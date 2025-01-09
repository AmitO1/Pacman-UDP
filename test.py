import cman_game
def dict_to_binary_string(coord_dict):
    # Create the binary string from the values in the dictionary
    binary_string = ''.join(str(coord_dict[coord]) for coord in coord_dict)

    return binary_string

points= cman_game.Game('map.txt').get_points()
points_str = dict_to_binary_string(points)
print(f"dict len: {len(points)}, stirng len: {len(points_str)}")

points[(13,16)] = 0
if (13,16) in points:
    print("yes boy")