#!/usr/bin/env python
# -*- coding: utf-8 -*-

########################################################################
#
# Zerg2Win AI
#
########################################################################

import random
from Queue import PriorityQueue
import operator

class AI:
    """Pure random A.I, you may NOT use it to win ;-)"""
    def __init__(self):
        pass

    def process(self, game):
        """Do whatever you need with the Game object game"""
        self.game = game
        self.obstacles = self.game.mines_locs + self.game.taverns_locs + self.game.walls_locs

    def manhattanDist(self, pos1, pos2):
        """Returns the manhattan distance between pos1 and pos2"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def getWalkableAdjacents(self, pos):
        """Returns walkable adjacent positions w.r.t to pos"""
        #1. Get adjacent nodes
        adjacents = []
        adjacents.append((pos[0], pos[1] - 1))
        adjacents.append((pos[0], pos[1] + 1))
        adjacents.append((pos[0] + 1, pos[1]))
        adjacents.append((pos[0] - 1, pos[1]))
        #2. Determine the walkable ones
        walkableAdjacents = []
        for node in adjacents:
            if node not in self.obstacles:
                if (node[0] >-1 and node[0] < self.game.board_size) and (node[1] >-1 and node[1] < self.game.board_size):
                    walkableAdjacents.append(node)
        return walkableAdjacents

    def findPath(self, start, goal):
        """Finds a path between start and goal using A*"""
        frontier = PriorityQueue()
        frontier.put(start, 0)
        came_from = {}
        cost_so_far = {}
        came_from[start] = None
        cost_so_far[start] = 0
        cost = 1

        while not frontier.empty():
            current = frontier.get()

            #2nd control is necessary for taverns&mines
            if current == goal or (goal in self.obstacles and self.manhattanDist(current, goal) == 1):
                data = []
                if current != goal:
                    data.append(goal)
                while current in came_from:
                    data.append(current)
                    current = came_from[current]
                data.reverse()
                return data[1:]

            for node in self.getWalkableAdjacents(current):
                new_cost = cost_so_far[current] + cost
                if node not in cost_so_far or new_cost < cost_so_far[node]:
                    cost_so_far[node] = new_cost
                    priority = new_cost + self.manhattanDist(goal, node)
                    frontier.put(node, priority)
                    came_from[node] = current
        return None

    def getMove(self, path_to_goal):
        """ Returns a valid command from one of [North, East, South, West, Stay] """
        if path_to_goal is None or len(path_to_goal) == 0:
            return "Stay"
        elif (len(path_to_goal) > 0):
            nextMove = path_to_goal[0]
            heroPos =  self.game.hero.pos
            dx = nextMove[1] - heroPos[1]
            dy = nextMove[0] - heroPos[0]
            if (dx == 0 and dy == 1):
                return "South"
            elif (dx == 0 and dy == -1):
                return "North"
            elif (dx == 1 and dy == 0):
                return "East"
            elif (dx == -1 and dy == 0):
                return "West"
            elif (dx == 0 and dy == 0):
                return "Stay"

    def orderByDistance(self, pos, places):
        """ Orders places by distance w.r.t to pos """
        return sorted(places, key=lambda item:self.manhattanDist(pos, item))

    def decide(self):
        """
        Must return a tuple containing in that order:
          1 - path_to_goal :
                  A list of coordinates representing the path to your
                 bot's goal for this turn:
                 - i.e: [(y, x) , (y, x), (y, x)]
                 where y is the vertical position from top and x the
                 horizontal position from left.

          2 - action:
                 A string that will be displayed in the 'Action' place.
                 - i.e: "Go to mine"

          3 - decision:
                 A list of tuples containing what would be useful to understand
                 the choice you're bot has made and that will be printed
                 at the 'Decision' place.

          4- hero_move:
                 A string in one of the following: West, East, North,
                 South, Stay

          5 - nearest_enemy_pos:
                 A tuple containing the nearest enenmy position (see above)

          6 - nearest_mine_pos:
                 A tuple containing the nearest enenmy position (see above)

          7 - nearest_tavern_pos:
                 A tuple containing the nearest enenmy position (see above)
        """

        actions = ['mine', 'tavern', 'fight']
        decisions = {'mine': [("Mine", 30), ('Fight', 10), ('Tavern', 5)],
                    'tavern': [("Mine", 10), ('Fight', 10), ('Tavern', 50)],
                    'fight': [("Mine", 15), ('Fight', 30), ('Tavern', 10)]}
        dirs = ["North", "East", "South", "West", "Stay"]

        """Find nearest enemy/mine/tavern"""
        enemies_by_distance = self.orderByDistance(self.game.hero.pos, self.game.heroes_locs)
        mines_by_distance =  self.orderByDistance(self.game.hero.pos, self.game.mines_locs)
        taverns_by_distance = self.orderByDistance(self.game.hero.pos, self.game.taverns_locs)
        nearest_enemy_pos = enemies_by_distance[0]
        nearest_mine_pos = mines_by_distance[0]
        nearest_tavern_pos = taverns_by_distance[0]
        available_mines_by_distance = []
        for mine in mines_by_distance:
            if mine not in self.game.hero.mines:
                available_mines_by_distance.append(mine)
        path_to_goal = []
        #this is to prevent crash if hero conquers all the mines
        if available_mines_by_distance == []:
            available_mines_by_distance.append(self.game.hero.pos)


        """Game logic begins here"""
        #1. If hp is below 60 (can be killed with 3 hits) and have money to afford tavern, go to tavern
        if self.game.hero.life <= 60 and self.game.hero.gold >= 2:
            path_to_goal = self.findPath(self.game.hero.pos, nearest_tavern_pos)
            action = actions[1]
        #2. If the nearest enemy owns mine or mines and closer than the nearest available mine, go after him
        else:
            for enemy in self.game.heroes:
                #the nearest enemy
                if enemy.pos == nearest_enemy_pos and (self.manhattanDist(self.game.hero.pos, enemy.pos) <= self.manhattanDist(self.game.hero.pos, available_mines_by_distance[0])):
                    if enemy.mine_count > 0:
                        path_to_goal = self.findPath(self.game.hero.pos, nearest_enemy_pos)
                        action = actions[2]
                        break
        #3. Just go after the nearest available mine if above cases fail
        if path_to_goal == []:
            path_to_goal = self.findPath(self.game.hero.pos,  available_mines_by_distance[0])
            action = actions[0]
        """Game logic ends here"""    

        action = actions[0]
        hero_move = self.getMove(path_to_goal)
        decision = decisions[action]

        #4. Error checking
        if hero_move == None:
             hero_move = random.choice(dirs)

        return (path_to_goal,
                action,
                decision,
                hero_move,
                nearest_enemy_pos,
                nearest_mine_pos,
                nearest_tavern_pos)


if __name__ == "__main__":
    pass
