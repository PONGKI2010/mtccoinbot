import nextcord
from nextcord.ext import commands
import sqlite3

intents = nextcord.Intents.default()
intents.typing = False
intents.presences = False
bot = commands.Bot(command_prefix='/', intents=intents)

# 데이터베이스 연결 (SQLite 사용)
conn = sqlite3.connect('coin_system.db')
c = conn.cursor()

# 테이블 생성 (최초 실행 시에만 필요)
c.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER,
    coins INTEGER
)''')

@bot.event
async def on_ready():
    print(f'봇 {bot.user} 로그인 성공!')

# 초기 코인 가치 설정
coin_value = 100  # 시작 가치 설정 (원하는 초기 가치로 변경)

# 관리자 역할 (2명 이상)
admin_roles = [1152204558722932746, 234567890123456789]  # 여기에 관리자 역할의 ID를 넣으세요.

# 3번째 구매자 카운터 초기화
third_buyer_counter = 0

@bot.slash_command(name='정보', description='잔액 및 보유 코인 확인')
async def 정보(interaction):
    user_id = interaction.user.id
    c.execute('SELECT balance, coins FROM users WHERE user_id = ?', (user_id,))
    user_data = c.fetchone()

    if user_data:
        balance, coins = user_data
        await interaction.send(f'**```css\n[ ✅ ] 잔액: {balance}원\n[ ✅ ] 보유 코인: {coins}개\n[ ✅ ] 코인 가치: {coin_value}원```**')
    else:
        await interaction.send('**```css\n[ ⛔ ] 사용자 정보를 찾을 수 없습니다. 등록을 해주세요.```**')

@bot.slash_command(name='등록', description='사용자 등록')
async def 등록(interaction):
    user_id = interaction.user.id
    c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    existing_user = c.fetchone()
    if not existing_user:
        c.execute('INSERT INTO users (user_id, balance, coins) VALUES (?, 0, 0)', (user_id,))
        conn.commit()
        await interaction.send('**```css\n[ ✅ ] 사용자 등록이 완료되었습니다.```**')
    else:
        await interaction.send('**```css\n[ ⛔ ] 이미 등록된 사용자입니다.```**')

@bot.slash_command(name='충전', description='사용자 잔액 충전')
async def 충전(interaction, user: nextcord.User, amount: int):
    if interaction.user.id in admin_roles:
        user_id = user.id
        c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        user_data = c.fetchone()

        if user_data:
            current_balance = user_data[0]
            new_balance = current_balance + amount
            c.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
            conn.commit()
            await interaction.send(f'**```css\n[ ✅ ] {user.display_name} 님의 잔액이 {amount}원 충전되었습니다.```**')
        else:
            await interaction.send('**```css\n[ ⛔ ] 사용자 정보를 찾을 수 없습니다.```**')
    else:
        await interaction.send('**```css\n[ ⛔ ] 권한이 없습니다.```**')

@bot.slash_command(name='구입', description='코인 구매')
async def 구입(interaction, coin_quantity: int):
    user_id = interaction.user.id
    c.execute('SELECT balance, coins FROM users WHERE user_id = ?', (user_id,))
    user_data = c.fetchone()

    if user_data:
        balance, coins = user_data
        global coin_value

        # 3번째 구매자가 등록될 때마다 가치를 100원씩 증가시킵니다.
        global third_buyer_counter
        third_buyer_counter += 1
        if third_buyer_counter % 3 == 0:
            coin_value += 100

        total_cost = coin_quantity * coin_value

        if balance >= total_cost:
            new_balance = balance - total_cost
            new_coins = coins + coin_quantity

            c.execute('UPDATE users SET balance = ?, coins = ? WHERE user_id = ?', (new_balance, new_coins, user_id))
            conn.commit()
            await interaction.send(f'**```css\n[ ✅ ] {coin_quantity}개의 코인을 {total_cost}원에 구매하였습니다.```**')
        else:
            await interaction.send('**```css\n[ ⛔ ] 잔액이 부족합니다.```**')
    else:
        await interaction.send('**```css\n[ ⛔ ] 사용자 정보를 찾을 수 없습니다. 등록을 해주세요.```**')

# 판매할 때 코인 가치를 300원씩 감소시키도록 수정
@bot.slash_command(name='판매', description='코인 판매')
async def 판매(interaction, coin_quantity: int):
    user_id = interaction.user.id
    c.execute('SELECT balance, coins FROM users WHERE user_id = ?', (user_id,))
    user_data = c.fetchone()

    if user_data:
        balance, coins = user_data
        global coin_value

        # 3번째 구매자가 등록될 때마다 가치를 100원씩 증가시킵니다.
        global third_buyer_counter
        third_buyer_counter += 1
        if third_buyer_counter % 3 == 0:
            coin_value += 100

        # 판매할 때 코인 가치를 300원씩 감소시킵니다.
        coin_value -= 300

        total_earnings = coin_quantity * coin_value

        if coins >= coin_quantity:
            new_balance = balance + total_earnings
            new_coins = coins - coin_quantity

            c.execute('UPDATE users SET balance = ?, coins = ? WHERE user_id = ?', (new_balance, new_coins, user_id))
            conn.commit()
            await interaction.send(f'**```css\n[ ✅ ] {coin_quantity}개의 코인을 {total_earnings}원에 판매하였습니다.```**')
        else:
            await interaction.send('**```css\n[ ⛔ ] 보유 코인이 부족합니다.```**')
    else:
        await interaction.send('**```css\n[ ⛔ ] 사용자 정보를 찾을 수 없습니다. 등록을 해주세요.```**')

@bot.slash_command(name='빼기', description='사용자 잔액 차감 (관리자 전용)')
async def 빼기(interaction, user: nextcord.User, amount: int):
    if interaction.user.id in admin_roles:
        user_id = user.id
        c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        user_data = c.fetchone()

        if user_data:
            current_balance = user_data[0]
            if current_balance >= amount:
                new_balance = current_balance - amount
                c.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
                conn.commit()
                await interaction.send(f'**```css\n[ ✅ ] {user.display_name} 님의 잔액에서 {amount}원을 차감하였습니다.```**')
            else:
                await interaction.send('**```css\n[ ⛔ ] 잔액이 부족합니다.```**')
        else:
            await interaction.send('**```css\n[ ⛔ ] 사용자 정보를 찾을 수 없습니다.```**')
    else:
        await interaction.send('**```css\n[ ⛔ ] 권한이 없습니다.```**')

# 봇 토큰을 여기에 추가하세요.
bot.run('MTE4MDcyMjU5MzIzMDI0MTg2Mg.GjYzXf.2aQ8aeyPeZeJigrfNXYnBwZn5qVwhDGANBVFCA')

