CMAN_CHAR = 'C'
SPIRIT_CHAR = 'S'
PLAYER_CHARS = [CMAN_CHAR, SPIRIT_CHAR]
POINT_CHAR = 'P'
FREE_CHAR = 'F'
PASS_CHARS = [CMAN_CHAR, SPIRIT_CHAR, POINT_CHAR, FREE_CHAR]
WALL_CHAR = 'W'
MAX_POINTS = 40

def read_map(path):
    """

    Reads map data and asserts that it is valid.

    Parameters:

    path (str): path to the textual map file

    """
    with open(path, 'r') as f:
        map_data = f.read()

        map_chars = set(map_data)
        assert map_chars.issubset({CMAN_CHAR, SPIRIT_CHAR, POINT_CHAR, WALL_CHAR, FREE_CHAR, '\n'}), "invalid char in map."
        assert map_data.count(CMAN_CHAR) == 1, "Map needs to have a single C-Man starting point."
        assert map_data.count(SPIRIT_CHAR) == 1, "Map needs to have a single Spirit starting point."
        assert map_data.count(POINT_CHAR) == MAX_POINTS, f"Map needs to have {MAX_POINTS} score points."

        map_lines = map_data.split('\n')
        assert all(len(line) == len(map_lines[0]) for line in map_lines), "map is not square."
        assert len(map_lines) < 2**8, "map is too tall"
        assert len(map_lines[0]) < 2**8, "map is too wide"

        sbc = all(line.startswith(WALL_CHAR) and line.endswith(WALL_CHAR) for line in map_lines)
        tbc = map_lines[0] == WALL_CHAR*len(map_lines[0]) and map_lines[-1] == WALL_CHAR*len(map_lines[-1])
        bbc = map_lines[0] == WALL_CHAR*len(map_lines[0]) and map_lines[-1] == WALL_CHAR*len(map_lines[-1])
        assert sbc and tbc and bbc, "map border is open."

        return map_data
    
def transform_map(map_string):
    """
    Transforms the input map string to a visually formatted version.

    Args:
        map_string (str): A string representation of the map, where:
                          - 'F' represents free space
                          - 'W' represents a wall
                          - 'P' represents a point
                          - 'C' represents cman location
                          - 'S' represents ghost location

    Returns:
        str: A transformed map string with visual formatting.
    """
    # Split the map string into lines
    map_lines = map_string.splitlines()
    
    # Calculate the dimensions of the map
    rows = len(map_lines)
    cols = max(len(line) for line in map_lines)

    # Initialize an empty list for the transformed map
    transformed_lines = []

    # Process each row in the map
    for i, line in enumerate(map_lines):
        transformed_line = []
        for j, char in enumerate(line):
            if char == 'F':
                transformed_line.append(' ')  # Free space becomes an empty char
            elif char == 'W':
                # Determine if the wall should be '|' or '-'
                if i == 0 or i == rows - 1:
                    transformed_line.append('-')  # Top and bottom walls are horizontal
                elif j == 0 or j == len(line) - 1:
                    transformed_line.append('|')  # Left and right walls are vertical
                elif (j > 0 and j < cols - 1 and line[j - 1] == 'W' and line[j + 1] == 'W'):
                    transformed_line.append('-')  # Horizontal walls in the middle
                elif (i > 0 and i < rows - 1 and len(map_lines[i - 1]) > j and map_lines[i + 1][j] == 'W'):
                    transformed_line.append('|')  # Vertical walls in the middle
                else:
                    transformed_line.append('-')  # Default to horizontal for isolated walls
            elif char == 'P':
                transformed_line.append('*')  # Point becomes '*'
            elif char == 'C':
                transformed_line.append('C')  # cman location remains 'C'
            elif char == 'S':
                transformed_line.append('S')  # Ghost location remains 'S'
            else:
                transformed_line.append(' ')  # Default to space for unknown characters
        # Join the transformed line and append to the list
        transformed_lines.append(''.join(transformed_line))

    # Join all the transformed lines with newline characters
    return '\n'.join(transformed_lines)