import discord
from discord.ext import commands
import requests
from lxml import html
from bs4 import BeautifulSoup
import logging
import random
import asyncpraw

# Stuff to setup the client 
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='$', intents=intents)  # Change this line



# Functions to find the distro info (Credits to @igoro00) on GitHub for inspiration
async def search(distro):
    try:
        output = {}
        mainurl = 'https://distrowatch.com'
        page = requests.get(f'https://distrowatch.com/table.php?distribution={distro.replace(" ", "+")}')
        tree = html.fromstring(page.content)
        output["logo"] = mainurl + tree.xpath("//td[@class='TablesTitle']/img")[0].attrib["src"]
        output["Name"] = tree.xpath("//td[@class='TablesTitle']/h1")[0].text
        info_elements = tree.xpath("//td[@class='TablesTitle']/ul/li")  # Get all information elements
        for element in info_elements:
            label, value = element.text_content().split(': ', 1)  # Split label and value
            output[label.strip()] = value.strip()  # Store label and value in the output dictionary
        return output
    except Exception as e:
        return None

# Function to extract distribution description from HTML content
def get_distribution_description(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    td_tag = soup.find('td', class_='TablesTitle')
    if td_tag:
        ul_tag = td_tag.find('ul')
        if ul_tag:
            description_text = ul_tag.find_next_sibling(string=True)
            if description_text:
                return description_text.strip()
    return "Description not found"

# Function to get distribution logo (Ignore)
def get_distribution_logo(distro):
    return f"https://distrowatch.com/images/yvzhuwbpy/{distro.lower()}.png"  # Dynamic logo URL based on distro name


# Function to get the top distros
async def topdistros():
    try:
        page = requests.get('https://distrowatch.com/')
        tree = html.fromstring(page.content)
        distros = tree.xpath("//td[@class='phr2']/a/text()")[:10]  # Get the top 10 distros
        formatted_distros = [f"{i+1}-{distro.capitalize()}" for i, distro in enumerate(distros)]
        # Join the formatted items into a single string
        formatted_list = '\n'.join(formatted_distros)
        # Create an embed
        embed = discord.Embed(title="Top distros in the last 6 months", description=formatted_list, color=0x0099ff)
        return embed
    except Exception as e:
        return None

def get_random_distribution():
    try:
        page = requests.get('https://distrowatch.com/')
        tree = html.fromstring(page.content)
        distros = tree.xpath("//td[@class='phr2']/a/text()")
        return random.choice(distros)
    except Exception as e:
        print(f"An error occurred while fetching random distribution: {e}")
        return None

# Bot commands:
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$find'):
        distro = message.content.split('$find')[1].strip()
        distro_info = await search(distro)
        if distro_info:
            embed = discord.Embed(title="Distro Information", color=0x0099ff)
            for key, value in distro_info.items():
                if key == 'logo':
                    embed.set_thumbnail(url=value)
                else:
                    embed.add_field(name=key, value=value, inline=False)
            await message.channel.send(embed=embed)
        else:
            await message.channel.send(f"Cannot find information for {distro}. Make sure you typed it correctly.")

    elif message.content.startswith('$explain'):
        distro = message.content.split('$explain')[1].strip()
        html_content = requests.get(f'https://distrowatch.com/table.php?distribution={distro.replace(" ", "+")}').text
        distro_description = get_distribution_description(html_content)
        if distro_description:
            distro_info = await search(distro)
            embed = discord.Embed(title=distro_info['Name'], description=distro_description, color=0x0099ff)
            embed.set_thumbnail(url=distro_info.get("logo", ""))
            await message.channel.send(embed=embed)
        else:
            await message.channel.send(f"Cannot find description for {distro}. Make sure you typed it correctly.")

    elif message.content.startswith('$top'):  
        embed = await topdistros()
        await message.channel.send(embed=embed)

    elif message.content.startswith('$logo'):
        distro = message.content.split('$logo')[1].strip()
        logo_url = get_distribution_logo(distro)
        if logo_url:
            await message.channel.send(f"{distro.capitalize()} Logo: {logo_url}")
        else:
            await message.channel.send(f"Cannot find logo for {distro}. Make sure you typed it correctly.")

    elif message.content.startswith('$random'):
        distro_name = get_random_distribution()
        if distro_name:
            html_content = requests.get(f'https://distrowatch.com/table.php?distribution={distro_name.replace(" ", "+")}').text
            distro_description = get_distribution_description(html_content)
            if distro_description:
                embed = discord.Embed(title=distro_name, description=distro_description, color=0x0099ff)
                await message.channel.send(embed=embed)
            else:
                await message.channel.send(f"Cannot find description for {distro_name}. Make sure you typed it correctly.")
        else:
            await message.channel.send("Failed to fetch a random distribution.")


@client.event
async def on_ready():
    #custom status
    activity = discord.Game(name="DistroFind")
    # Set the custom status
    await client.change_presence(activity=activity)
# Run the client
#--------------------------------------------------------
client.run('YOUR_TOKEN_HERE')
#--------------------------------------------------------
logging.getLogger('requests').setLevel(logging.WARNING)
