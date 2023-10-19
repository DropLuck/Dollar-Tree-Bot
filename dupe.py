import discord
import asyncio 
import requests 
import json 
import motor 
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorClient 
from discord.ext import commands
from discord import Option
from itertools import cycle
from discord.ext import tasks
import random
import string
import time 

from discord import Intents

intents = discord.Intents.all()

bot = discord.Bot(Intents=intents)

TOKEN = 'YOUR TOKEN'

client = discord.Client()

bot_status = cycle(["/login", "/dupe", "/logout", "Drop>PuggyWuggy"])

@tasks.loop(seconds=1)
async def change_status():
    await bot.change_presence(activity=discord.Game(next(bot_status)))

@bot.event
async def on_ready():
    print("Bot Is Connected To Discord!")
    change_status.start()

DATABASE_CLUSTER = AsyncIOMotorClient("mongodb+srv://USERNAME:PASSWORD@morbdupebot.eehucv5.mongodb.net/?retryWrites=true&w=majority")
db = DATABASE_CLUSTER["Fenex"]
user_data = db["USER_DATA"]

import aiohttp


# UTILS

async def FetchAvatarUser(user_id):
    Account_Check = await user_data.find_one({"UserId": user_id})

    token_ref = Account_Check['AccessToken']
    accountid = Account_Check['AccountId']
    
    headers = {"Authorization": f"Bearer {token_ref}"}
    url = f"https://avatar-service-prod.identity.live.on.epicgames.com/v1/avatar/fortnite/ids?accountIds={accountid}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            idavatar = data[0]['avatarId']
            idavatar = idavatar.replace('ATHENACHARACTER:', '')
            
            return f"https://fortnite-api.com/images/cosmetics/br/{idavatar}/icon.png"

async def UpdateInfoAccount(user_id):
    Account_Check = await user_data.find_one({"UserId": user_id})

    accountid = Account_Check['AccountId']
    deviceId = Account_Check['DeviceId']
    secret = Account_Check['Secret']
    
    session = aiohttp.ClientSession()
    
    async with session.post("https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token", data=f"grant_type=device_auth&account_id={accountid}&device_id={deviceId}&secret={secret}",headers={'Content-Type': 'application/x-www-form-urlencoded','Authorization': f'basic MzQ0NmNkNzI2OTRjNGE0NDg1ZDgxYjc3YWRiYjIxNDE6OTIwOWQ0YTVlMjVhNDU3ZmI5YjA3NDg5ZDMxM2I0MWE='}) as r:
        if r.status == 200:
            data = await r.json()
            access_code, display_name, account_id = data['access_token'], data['displayName'], data['account_id']
            
            DataInsert = {
                    "UserId": user_id, 
                    "AccessToken": access_code, 
                    "AccountId": account_id, 
                    "DisplayName": display_name,
                    "DeviceId": deviceId, 
                    "Secret": secret
                }

            await user_data.update_one({"UserId": user_id}, {"$set": DataInsert})                
            await session.close()
    
################################################################################################################################
    
    
    
#Embed Error(s)

UnknownError = discord.Embed(title=f"Authorization Error ❌",description="Drop's Bot needs a new authorization code. Logout and log back in with a new auth.",colour= discord.Colour.brand_red())    
NotLoggedIn = discord.Embed(description="**`❌ Not Logged In, Try /login ❌`**",colour=discord.Colour.red())
YouCannotDoThis = discord.Embed(title= "Access DENIED ❌", description= "You cannot do this command.",colour=discord.Colour.red())
YouAreNotWhitelisted = discord.Embed(title= "ACCESS DENIED ❌", description= "**You Are NOT Whitelisted**")

#Reload 

@bot.slash_command(name = "reload", description = "Reloads all  commands.")
async def reload(ctx):
    if ctx.author.id == 480398311841464321:
        embed1 = discord.Embed(title="Reloading...", color=0x0091ff)
        embed2 = discord.Embed(title="Reloaded ✅", color=0x0091ff)
        embed3 = discord.Embed(title=f"Reload complete, {bot.user}!", color=0x0091ff)
        await ctx.respond(embed=embed1)
        bot.reload_extension
        embed2 = discord.Embed(title=f"Reloaded!", color=0x0091ff)
        await ctx.edit(embed=embed2)
        await ctx.edit(embed=embed3)

    else:
        await ctx.respond("You are not a dev.", ephemeral=True)


#Login 


class Login(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Authorization Code."))


    async def callback(self, interaction: discord.Interaction):
        Data_Check = await user_data.find_one({"UserId": interaction.user.id})
        if Data_Check is None:
            try:
                
                HeaderData = {
                    "Content-Type": f"application/x-www-form-urlencoded",
                    "Authorization": f"basic MzQ0NmNkNzI2OTRjNGE0NDg1ZDgxYjc3YWRiYjIxNDE6OTIwOWQ0YTVlMjVhNDU3ZmI5YjA3NDg5ZDMxM2I0MWE="
                }
                LoginData = f"grant_type=authorization_code&code={self.children[0].value}"
                LoginRequest = requests.post("https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token",headers=HeaderData,data=LoginData)
                
                display_name = LoginRequest.json()['displayName']
                accountId = LoginRequest.json()['account_id']
                access_code = LoginRequest.json()['access_token']
                
                headers = {'Authorization': f'Bearer {access_code}'}
                response = requests.post(url=f'https://account-public-service-prod.ol.epicgames.com/account/api/public/account/{accountId}/deviceAuth', headers=headers)
                device_id, secret = response.json()['deviceId'], response.json()['secret']


                DataInsert = {
                    "UserId": interaction.user.id, 
                    "AccessToken": access_code, 
                    "AccountId": accountId, 
                    "DisplayName": display_name,
                    "DeviceId": device_id, 
                    "Secret": secret
                }

                await user_data.insert_one(DataInsert)
                
                avatar = await FetchAvatarUser(interaction.user.id)
                


                embed = discord.Embed(
                    title=f"You are now logged in as, `{display_name}`",
                    description="You have been added to our databases.",
                    colour= discord.Colour.brand_green()
                )
                embed.set_thumbnail(url=avatar)

                    
                await interaction.response.send_message(embeds=[embed])

            except:
                await interaction.respond.send_message("Authorization Code Expired.")
                
        else:
            embed = discord.Embed(title="Logged In Already.",description=f"You are already logged in as, `{Data_Check['DisplayName']}`",colour=discord.Colour.green())
            await interaction.response.send_message(embeds=[embed]) 



class LoginGUI(discord.ui.View):  # Create a class called MyView that subclasses discord.ui.View

    @discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
    async def button_callback(self, button, interaction: discord.Interaction):
        modal = Login(title="Authorization Code")
        await interaction.response.send_modal(modal)


@bot.slash_command(description="Login to your fortnite account.")
async def login(ctx):
    GUI = LoginGUI()
    Add_Component = GUI.add_item(discord.ui.Button(label="Authorization Code", style=discord.ButtonStyle.link, url="https://www.epicgames.com/id/api/redirect?clientId=3446cd72694c4a4485d81b77adbb2141&responseType=code"))
    embed = discord.Embed(
        title="**`Login Process.`**",
        description="To login follow these steps to login :\n\n`1.` Click The Button Named Authorization Code\n\n`2.` Copy Your Authorization Code\n\n`3.` Paste Your Authorization Code in Submit\n\nWrong Account or authorizationCode shows null try [this](https://www.epicgames.com/id/login?redirectUrl=https%3A%2F%2Fwww.epicgames.com%2Fid%2Fapi%2Fredirect%3FclientId%3D3446cd72694c4a4485d81b77adbb2141%26responseType%3Dcode)",
        colour = discord.Colour.brand_green(),
    )
    await ctx.respond(embed=embed, view=GUI)
    
    
#Logout Command



@bot.slash_command(description="Log out of your fortnite account.")
async def logout(ctx):
    
    Data_Check = await user_data.find_one({"UserId": ctx.author.id})
    if Data_Check is None:
        await ctx.respond(embed=NotLoggedIn)
    else:
        await user_data.delete_one({"UserId": ctx.author.id})
        embed = discord.Embed(title="Logged Out.",description="You are now logged out!",colour=discord.Colour.green())
        await ctx.respond(embed=embed)

#Clear Friends


@bot.slash_command(name="clear-friends", description="Clears all friends.")
async def clear_friends(ctx):
    
    await ctx.defer()

    Account_Check = await user_data.find_one({"UserId": ctx.author.id})
    if Account_Check is None:
        await ctx.respond(embed=NotLoggedIn)
        
    else:
        await UpdateInfoAccount(ctx.author.id)

        
        token_ref = Account_Check['AccessToken']
        accountid = Account_Check['AccountId']
        
        avatar = await FetchAvatarUser(ctx.author.id)
        
        headers = {
            "Authorization": f"Bearer {token_ref}"
        }
        deletereq = requests.delete(f"https://friends-public-service-prod.ol.epicgames.com/friends/api/v1/{accountid}/friends", headers=headers)
                    
        embed = discord.Embed(description="Cleared All Friends!", colour=discord.Colour.green())
        embed.set_thumbnail(url=avatar)
        await ctx.respond(embed=embed)
        
  
  #Show Current Account


@bot.slash_command(description="View account.")
async def who(ctx):
    await ctx.defer()
    
    Account_Check = await user_data.find_one({"UserId": ctx.author.id})
    if Account_Check is None:
        await ctx.respond(embed=NotLoggedIn)
        
    else:
        await UpdateInfoAccount(ctx.author.id)
        
        display_name = Account_Check['DisplayName']

        avatar = await FetchAvatarUser(ctx.author.id)
        
        embed = discord.Embed(description=f"You are logged in as **{display_name}**", colour=discord.Colour.blue())
        embed.set_thumbnail(url=avatar)
        await ctx.respond(embed=embed)


#Ventures
        

@bot.slash_command(name="vdupe", description="Enables the venture dupe.")
async def vdupe(ctx):
    try:
        await ctx.defer()
        
        Account_Check = await user_data.find_one({"UserId": ctx.author.id})

        if Account_Check is None:
            await ctx.respond(embed=NotLoggedIn)
        else:
            
            await UpdateInfoAccount(ctx.author.id)

            items_dupeventure = []

            token_ref = Account_Check['AccessToken']
            accountid = Account_Check['AccountId']
            headers = {
                "Content-Type": f"application/json",
                "Authorization": f"Bearer {token_ref}"
            }
            data = json.dumps({})
            
            try:
                request = requests.post(f"https://fortnite-public-service-prod11.ol.epicgames.com/fortnite/api/game/v2/profile/" + accountid + "/client/QueryProfile?profileId=theater2&rvn=-1",headers=headers,data=data)
                res = request.json()
                
                stuff = res['profileChanges'][0]['profile']['items']
                
                for i in stuff:
                    if "building" in stuff[i]['templateId']:
                        items_dupeventure.append(i)
                        
                        
                if items_dupeventure == []:
                    embed = discord.Embed(title="PATCHED!", description="**THIS DUPE HAS BEEN PATCED! sorry not sorry 😂 **",colour=discord.Colour.red())
                    await ctx.respond(embed=embed)
                else:
                    body = json.dumps({"itemIds": [items_dupeventure]})
                                   
                    venturedestroyreq = requests.post(f"https://fortnite-public-service-prod11.ol.epicgames.com/fortnite/api/game/v2/profile/" + accountid + "/client/DestroyWorldItems?profileId=theater2&rvn=-1",headers=headers,data=body)
                    embed = discord.Embed(title="PATCHED!",description=f"**THIS DUPE HAS BEEN PATCED! sorry not sorry 😂 **\n\n**`{Account_Check['DisplayName']}`**",colour=discord.Color.green())
                    await ctx.respond(embed=embed)
                    items_dupeventure.clear()
            except:
                await ctx.respond(embed=UnknownError)
    except:
        await ctx.respond(embed=UnknownError)




#Leave


@bot.slash_command(description="Leave the fortnite party.")
async def leave(ctx):
    await ctx.defer()
    account_Check = await user_data.find_one({"UserId": ctx.author.id})
    
    if account_Check is None:
        await ctx.respond(embed=NotLoggedIn)
        
    else:
        await UpdateInfoAccount(ctx.author.id)

        token_ref = account_Check['AccessToken']
        accountid = account_Check['AccountId'] 
        
        headers = {"Authorization": f"Bearer {token_ref}"}
        url = f"https://party-service-prod.ol.epicgames.com/party/api/v1/Fortnite/user/{accountid}"
        response = requests.get(url, headers=headers)
        
        party = response.json()['current']
        
        if party == []:
            embed = discord.Embed(title="Error", description="You are not in a party.", color=discord.Color.red())
            await ctx.respond(embed=embed)
        else:
            party_id = party[0]['id']
            
            url = f"https://party-service-prod.ol.epicgames.com/party/api/v1/Fortnite/parties/{party_id}/members/{accountid}"
            response = requests.delete(url, headers=headers)
            
            embed = discord.Embed(title="Success", description=f"You have left the fortnite party.", color=discord.Color.green())
            await ctx.respond(embed=embed)
   

#DUPE

@bot.slash_command(name = "dupe", description = "Start the dupe.")
async def dupe(ctx):
    if ctx.author.id == 480398311841464321:
        embed1 = discord.Embed(title="Starting Dupe...", description="Please wait as the bot starts the dupe.", color=discord.Color.blue())
        embed2 = discord.Embed(title="Dupe Enabled!", description="Your inventory has been saved, you can now drop anything that you want to dupe.", color=discord.Color.green())
        await ctx.respond(embed=embed1)
        bot.reload_extension
        embed2 = discord.Embed(title=f"Dupe Enabled!", description="**Your inventory has been saved, you can now drop anything that you want to dupe.**", color=discord.Color.green())
        await  ctx.respond(embed=embed2)

    else:
        embed1 = discord.Embed(title= "**You Are Not Whitelisted!** ❌", description= "You Must Be Whitelisted To Use `/dupe`",colour=discord.Colour.brand_red())
        await  ctx.respond(embed=embed1)

bot.run(TOKEN)
