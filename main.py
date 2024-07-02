import os
import discord
from discord.ext import commands
from discord import app_commands
import random
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.games = {}

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()

class MinesweeperButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=x)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id not in interaction.client.games:
            await interaction.response.send_message('You have no ongoing game! Use /gamble to start a new game.', ephemeral=True)
            return

        game = interaction.client.games[user_id]
        board = game['board']
        mines = game['mines']
        revealed = game['revealed']

        if (self.x, self.y) in revealed:
            await interaction.response.send_message('This cell is already revealed!', ephemeral=True)
            return

        if (self.x, self.y) in mines:
            # Reveal all mines
            for mine in mines:
                game['board'][mine[0]][mine[1]] = '💣'
            # Update button styles
            for child in self.view.children:
                if isinstance(child, MinesweeperButton):
                    if (child.x, child.y) in mines:
                        child.style = discord.ButtonStyle.danger
                        child.label = '💣'
                    elif (child.x, child.y) in revealed:
                        child.style = discord.ButtonStyle.success
                        child.label = '🟩'
            await interaction.response.edit_message(view=self.view)
            del interaction.client.games[user_id]
            return

        revealed.add((self.x, self.y))
        board[self.x][self.y] = '🟩'

        for child in self.view.children:
            if isinstance(child, MinesweeperButton) and (child.x, child.y) in revealed:
                child.style = discord.ButtonStyle.success
                child.label = '🟩'

        await interaction.response.edit_message(view=self.view)

class MinesweeperView(discord.ui.View):
    def __init__(self, board_size: int):
        super().__init__(timeout=None)
        for x in range(board_size):
            for y in range(board_size):
                self.add_item(MinesweeperButton(x, y))

@client.tree.command(name="gamble", description="Start a new game of Mines!")
async def gamble(interaction: discord.Interaction):
    user_id = interaction.user.id

    if user_id in interaction.client.games:
        await interaction.response.send_message('You already have an ongoing game! Use /click to play.', ephemeral=True)
        return

    board_size = 5
    mine_count = 5
    board = [['⬜' for _ in range(board_size)] for _ in range(board_size)]
    mines = set()

    while len(mines) < mine_count:
        x, y = random.randint(0, board_size-1), random.randint(0, board_size-1)
        mines.add((x, y))

    interaction.client.games[user_id] = {
        'board': board,
        'mines': mines,
        'revealed': set()
    }

    view = MinesweeperView(board_size)
    await interaction.response.send_message('Game started! Click on the buttons to select a cell.', view=view, ephemeral=True)


client.run(TOKEN)
