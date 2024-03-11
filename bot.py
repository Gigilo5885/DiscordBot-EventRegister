import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

DISCORD_TOKEN = DISCORD_TOKEN
GOOGLE_SHEETS_CREDS = GOOGLE_SHEETS_CREDS
GOOGLE_SHEETS_URL = GOOGLE_SHEETS_URL

@client.event
async def on_ready():
    print(f"已成功登入: {client.user.name} ({client.user.id})")
    game = discord.Game('準備中')
    await client.change_presence(status=discord.Status.idle, activity=game)


@client.event
async def on_message(message):
    try:
        content = str(message.content)
        print(f"收到信息: {content!r}")  # Debugging message

        if message.author == client.user or not content:
            return

        elif content.startswith('!register'):
            print("收到註冊命令")  # Debugging message

            command_args = content.split()[1:]

            if len(command_args) != 2:
                print("命令使用無效")  # Debugging message
                await message.channel.send('無效指令. 正確填寫方法為: `!register [名] [男/女]`')
                return

            name = command_args[0]
            gender = command_args[1]

            scope = ['https://www.googleapis.com/auth/spreadsheets']
            creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDS, scope)
            gc = gspread.authorize(creds)

            sheet = gc.open_by_url(GOOGLE_SHEETS_URL).worksheet('人員名單')
            users = sheet.get_all_records()

            for row in users:
                if row[1] == name:
                    await message.channel.send(f' {name} 已存在, 請使用其他名字')
                    return

            user_data = [name, gender]
            sheet.append_row(user_data)

            await message.channel.send(f'註冊成功！ 居民: {name} 性別: {gender}')
        elif content.startswith('!edit'):
            print("收到編輯命令")

            command_args = content.split()[1:]

            if len(command_args) != 3:
                print("命令使用無效")
                await message.channel.send('無效指令. 正確填寫方法為: `!edit [名] [新名] [新性別]`')
                return

            name = command_args[0]
            new_name = command_args[1]
            new_gender = command_args[2]

            scope = ['https://www.googleapis.com/auth/spreadsheets']
            creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDS, scope)
            gc = gspread.authorize(creds)

            sheet = gc.open_by_url(GOOGLE_SHEETS_URL).worksheet('人員名單')

            users = sheet.get_all_values()

            name_exists = False
            new_name_exists = False

            for row in users:
                if row[0] == name:
                    name_exists = True
                if row[0] == new_name and new_name != name:
                    new_name_exists = True

            if not name_exists:
                await message.channel.send(f'找不到居民: {name}')
                return
            elif new_name_exists:
                await message.channel.send(f'新名稱已存在: {new_name}')
                return

            edited = False
            for row_index, row in enumerate(users):
                if row[0] == name:
                    if new_name != name:
                        row[0] = new_name
                    row[1] = new_gender
                    range_name = f'A{row_index+1}:Z{row_index+1}'
                    sheet.update(range_name=range_name, values=[row])
                    edited = True
                    break

            if edited:
                await message.channel.send(f'編輯成功！ 居民: {name} 的姓名已被修改為 {new_name}，性別已被修改為 {new_gender}')
            else:
                await message.channel.send(f'找不到居民: {name}')

        elif content.startswith('!del'):
            print("收到刪除命令") 

            command_args = content.split()[1:]

            if len(command_args) != 1:
                print("命令使用無效") 
                await message.channel.send('無效指令. 正確填寫方法為: `!delete [名]`')
                return

            name = command_args[0]

            scope = ['https://www.googleapis.com/auth/spreadsheets']
            creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDS, scope)
            gc = gspread.authorize(creds)

            sheet = gc.open_by_url(GOOGLE_SHEETS_URL).worksheet('人員名單')
            users = sheet.get_all_records()

            deleted = False
            for index, row in enumerate(users, start=2): 
                if row['姓名'] == name:
                    sheet.delete_rows(index)
                    deleted = True
                    break

            if deleted:
                await message.channel.send(f'刪除成功！ 居民: {name} 已被刪除')
            else:
                await message.channel.send(f'找不到居民: {name} ')
                
        elif content.startswith('!book'):
            print("收到錄書命令")  

            command_args = content.split()[1:]

            if len(command_args) != 2:
                print("命令使用無效")
                await message.channel.send('無效指令. 正確填寫方法為: `!book [劇本名稱] [類別]`')
                return

            script_name = command_args[0]
            category = command_args[1]

            response_message = await message.channel.send('請問是否可以反串？\n✅：可以\n❌：不可以')

            await response_message.add_reaction('✅')
            await response_message.add_reaction('❌')

            def check(reaction, user):
                return user == message.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == response_message.id

            try:
                reaction, user = await bot.wait_for('reaction_add', check=check, timeout=60)
                reverse_role_emoji = str(reaction.emoji)
            except asyncio.TimeoutError:
                await message.channel.send('未收到回應，錄書已取消')
                return

            reverse_role_text = '是' if reverse_role_emoji == '✅' else '否'

            await message.channel.send('預訂成功！劇本已被添加到相應的頁面')

    except Exception as e:
        print(f"發生錯誤: {e}")


client.run(DISCORD_TOKEN)

