import json
import sys
import os
import requests
import discord
import datetime
from pymongo import MongoClient

#Discord client secret
discord_token = "NzM2NjQ2MDQ3MTUyOTk2NDEz.Xxx1Fw.t92jE1fdgc9DOjDC--zKMdjWhiU"

client = discord.Client()

myChessStats = None

@client.event
async def on_ready():
    global myChessStats
    myChessStats = ChessStats()
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):  # event that happens per any message.
    global myChessStats
    
    if message.content.startswith(".cset") and len(message.content.split()) > 1:
        out = myChessStats.cSet(
            str(message.author), 
            message.content.split(" ")[1].strip()
        )
        await message.channel.send(out)
        
    if message.content.startswith(".cstats"):
        author = str(message.author)
        
        if(not myChessStats.checkUser(str(author))):
            await message.channel.send("Please set your username first using .cbset <username>")
        else:
            await message.channel.send(embed = myChessStats.cStats(author))

    print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")
    
class ChessStats:
    
    def __init__(self):
        self.users = UserStorage()
        
    def cSet(self, discordName, chessName):
        checkName = requests.get("https://api.chess.com/pub/player/" + chessName).json()

        if not 'code' in checkName:
            self.users.setUser(discordName, chessName)
            return "Username set."

        return "User not found."

        
    def cStats(self, discordName):
        chessName = self.users.getUser(discordName)
        stats = self.getStats(chessName)

        statsEmbed = discord.Embed(title=chessName, url="https://www.chess.com/member/" + chessName)
        
        profile = requests.get("https://api.chess.com/pub/player/" + chessName).json()
        
        if 'avatar' in profile:
            statsEmbed.set_image(
                url=profile['avatar']
            )
        
        if 'chess_bullet' in stats:
            statsEmbed.add_field(
                name="Bullet",
                value = "Rating:\t" + str(stats['chess_bullet']['last']['rating']) + "\n" + self.getWLRatio(stats['chess_bullet'])
            )
            
        if 'chess_blitz' in stats:
            statsEmbed.add_field(
                name="Blitz",
                value = "Rating:\t" + str(stats['chess_blitz']['last']['rating']) + "\n" + self.getWLRatio(stats['chess_blitz'])
            )
            
        if 'chess_rapid' in stats:
            statsEmbed.add_field(
                name="Rapid",
                value = "Rating:\t" + str(stats['chess_rapid']['last']['rating']) + "\n" + self.getWLRatio(stats['chess_rapid'])
            )
            
        if 'chess_daily' in stats:
            statsEmbed.add_field(
                name="Daily", 
                value = "Rating:\t" + str(stats['chess_daily']['last']['rating']) + "\n" + self.getWLRatio(stats['chess_daily'])
            )
            
        prStats = ""
        hasPuzzleStats = False
        
        if 'daily' in stats['puzzle_rush']:
            prStats += "Daily\nAttempts: " + str(stats['puzzle_rush']['daily']['total_attempts']) + ", Score: " + str(stats['puzzle_rush']['daily']['score'] )+ '\n'
            hasPuzzleStats = True
            
        if 'best' in stats['puzzle_rush']:
            prStats += "Best\nAttempts: " + str(stats['puzzle_rush']['best']['total_attempts']) + ", Score: " + str(stats['puzzle_rush']['best']['score'])        
            hasPuzzleStats = True      
            
        if hasPuzzleStats:                                                                               
            statsEmbed.add_field(
                name="Puzzle Rush",
                value = prStats
            )

        statsEmbed.timestamp = datetime.datetime.now()

        return statsEmbed
   
    def getStats(self, chessName):
        return requests.get("https://api.chess.com/pub/player/" + chessName + "/stats").json() 
    
    def checkUser(self, discordName):
        return self.users.checkUser(discordName)
    
    def getWLRatio(self, data):
        win = data['record']['win']
        loss = data['record']['loss']
        draw = data['record']['draw']
        total = win + loss + draw
        
        wld = "Win:\t{winRatio:.0%} \nLoss:\t{lossRatio:.0%} \nDraw:\t{drawRatio:.0%}"
        
        prettyWld = wld.format(
            winRatio = win/total, 
            lossRatio = loss/total, 
            drawRatio = draw/total
        )
        
        return prettyWld
   
class UserStorage:

    def __init__(self):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client["bot"]
        self.userCol = self.db["users"] 

    #check if user exists
    def checkUser(self, discordName):
        nameQuery = {'discordName': str(discordName)}
        user = self.userCol.find_one(nameQuery)
        if user is not None:
            return True
        else:
            return False

    #add a new user
    def setUser(self, discordName, chessName):
        if not self.checkUser(discordName):
            user = {'discordName' : str(discordName), 'chessName' : str(chessName)}
            self.userCol.insert_one(user)
            print("user set")
        elif self.checkUser(discordName):
            print("updating")
            myquery = {'discordName': str(discordName)}
            self.userCol.update_one(myquery, {'$set':{ 'chessName': str(chessName)}})
        
    #return a users chess name
    def getUser(self, discordName):
        if self.checkUser(discordName):
            myquery = { 'discordName': str(discordName)}
            mydoc = self.userCol.find_one(myquery)
            return mydoc['chessName']
        else:
            return 

client.run(discord_token)