class LangtonsAnt:
    def __init__(self, width, height):
        self.width = width  # Width of the board
        self.height = height  # Height of the board
        self.ant_x = width // 2  # Initial horizontal position
        self.ant_y = height // 2  # Initial vertical position
        self.ant_dir = 0  # 0: right, 1: up, 2: left, 3: down
        self.grid = [[0 for _ in range(height)] for _ in range(width)]
        self.ant_colors = [(200, 0, 0), (0, 200, 0),
                           (0, 0, 200), (150, 100, 0)]
        self.trail = []  # Stores the last few positions of the ant

    def move(self):
        current_color = self.grid[self.ant_x][self.ant_y]
        # Decide the new direction of the ant based on the current cell color
        if current_color in [0, 1]:
            self.ant_dir = (self.ant_dir + 1) % 4  # turn right
        else:
            self.ant_dir = (self.ant_dir - 1) % 4  # turn left

        # Update the color of the current cell
        new_color = (current_color + 1) % 4
        self.grid[self.ant_x][self.ant_y] = new_color

        # Move the ant forward based on its current direction
        if self.ant_dir == 0:  # moving right
            self.ant_x = (self.ant_x + 1) % self.width
        elif self.ant_dir == 1:  # moving up
            self.ant_y = (self.ant_y - 1) % self.height
        elif self.ant_dir == 2:  # moving left
            self.ant_x = (self.ant_x - 1) % self.width
        elif self.ant_dir == 3:  # moving down
            self.ant_y = (self.ant_y + 1) % self.height

         # Append the current position to the trail
        self.trail.append((self.ant_x, self.ant_y, self.ant_colors[new_color]))
        # Only keep the last few positions in the trail
        trail_length = 3  # for example, keep the last 3 positions
        self.trail = self.trail[-trail_length:]

        return (self.ant_x, self.ant_y, self.ant_colors[new_color])

    def get_trail(self):
        return list(self.trail)
