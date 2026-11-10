import os
import re
import asyncio
import ipaddress
import socket
from urllib.parse import urlparse
import validators
import discord
from discord.ext import commands
from discord import app_commands
from playwright.async_api import async_playwright, Browser, Page

# ==================== CONFIG ====================
# Bạn có thể điền trực tiếp Token của bạn vào biến bên dưới (hoặc dùng biến môi trường)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN_HERE")

# Danh sách Channel ID được phép dùng bot (để trống [] nếu cho phép tất cả các kênh)
ALLOWED_CHANNEL_IDS = []

# Whitelist domain được phép xử lý
ALLOWED_DOMAINS = [
    "deltaexploits.net",
    "linkvertise.com",
    "lootdest.org",
    "bypass.city"
]

MAX_STEPS = 15
PAGE_TIMEOUT_SEC = 30

if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
    print("⚠️ CẢNH BÁO: Chưa cấu hình DISCORD_TOKEN hợp lệ!")

# ==================== SECURITY GUARD ====================
class SecurityGuard:
    @staticmethod
    def is_safe_url(url: str) -> tuple[bool, str]:
        if not validators.url(url):
            return False, "URL không hợp lệ hoặc sai định dạng."
        
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, "Chỉ chấp nhận URL sử dụng scheme HTTP hoặc HTTPS."
        
        hostname = parsed.hostname
        if not hostname:
            return False, "Không thể xác định domain từ URL."
            
        lower_host = hostname.lower()
        if lower_host in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return False, "Truy cập vào mạng nội bộ bị từ chối."
            
        try:
            ip = ipaddress.ip_address(socket.gethostbyname(hostname))
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False, "Địa chỉ IP đích nằm trong dải mạng nội bộ hoặc bị cấm."
        except (socket.gaierror, ValueError):
            pass

        allowed = False
        for allowed_domain in ALLOWED_DOMAINS:
            if lower_host == allowed_domain or lower_host.endswith("." + allowed_domain):
                allowed = True
                break
                
        if not allowed:
            return False, f"Domain `{hostname}` không nằm trong whitelist được phép xử lý."
            
        return True, "URL an toàn."

# ==================== BROWSER MANAGER ====================
class BrowserManager:
    def __init__(self):
        self._playwright = None
        self._browser: Browser = None

    async def init_browser(self):
        if not self._playwright:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-size=1280,720"
                ]
            )

    async def new_page(self) -> Page:
        await self.init_browser()
        context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="en-US"
        )
        return await context.new_page()

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

browser_manager = BrowserManager()

# ==================== PAGE HANDLERS ====================
class PageHandlers:
    @staticmethod
    async def detect_page_type(page: Page) -> str:
        content = await page.content()
        content_lower = content.lower()
        
        if "hcaptcha" in content_lower or "recaptcha" in content_lower or "cloudflare" in content_lower or "verify you are human" in content_lower:
            return "captcha"
            
        if "login" in content_lower and ("password" in content_lower or "sign in" in content_lower):
            return "login_required"

        if PageHandlers._extract_key_from_text(content):
            return "has_key"

        if "wait" in content_lower or "second" in content_lower or "countdown" in content_lower:
            for selector in [".timer", "#timer", "[id*='timer']", "[class*='timer']"]:
                if await page.locator(selector).count() > 0:
                    return "timer"

        for selector in ["button:has-text('Continue')", "a:has-text('Continue')", "button:has-text('Proceed')", "a:has-text('Skip')", "#continue-btn", ".continue-btn"]:
            if await page.locator(selector).count() > 0:
                return "interactive_button"

        return "unknown"

    @staticmethod
    async def handle_page(page: Page, page_type: str) -> tuple[bool, str]:
        try:
            if page_type == "captcha":
                return False, "Phát hiện CAPTCHA hoặc trang xác minh bảo mật. Vui lòng xử lý thủ công."
            if page_type == "login_required":
                return False, "Trang yêu cầu đăng nhập tài khoản. Bot không hỗ trợ bypass đăng nhập."
            if page_type == "timer":
                await page.wait_for_timeout(5000)
                return True, "Đã chờ bộ đếm thời gian."
            if page_type == "interactive_button":
                for selector in ["button:has-text('Continue')", "a:has-text('Continue')", "button:has-text('Proceed')", "a:has-text('Skip')", "#continue-btn", ".continue-btn"]:
                    loc = page.locator(selector).first
                    if await loc.is_visible():
                        await loc.click()
                        await page.wait_for_timeout(3000)
                        return True, "Đã click nút tiếp tục."
            return True, "Không có hành động đặc biệt, tiếp tục theo dõi."
        except Exception as e:
            return False, f"Lỗi khi xử lý handler ({page_type}): {str(e)}"

    @staticmethod
    def _extract_key_from_text(html_content: str) -> str | None:
        if "delta" in html_content.lower() or "key" in html_content.lower():
            match = re.search(r'(?:delta|key)[\s:]*([A-Za-z0-9\-_]{20,})', html_content, re.IGNORECASE)
            if match:
                val = match.group(1)
                if len(val) >= 20:
                    return val
        return None

# ==================== DELTA RESOLVER ====================
class DeltaResolver:
    @staticmethod
    async def resolve(url: str, status_callback) -> tuple[bool, str]:
        is_safe, msg = SecurityGuard.is_safe_url(url)
        if not is_safe:
            return False, f"Vi phạm bảo mật: {msg}"

        page = await browser_manager.new_page()
        steps = 0

        try:
            await status_callback("🔍 Đang khởi tạo trình duyệt và truy cập link ban đầu...")
            await page.goto(url, timeout=PAGE_TIMEOUT_SEC * 1000, wait_until="domcontentloaded")

            while steps < MAX_STEPS:
                steps += 1
                await status_callback(f"🔄 Đang xử lý bước {steps}/{MAX_STEPS} (URL: {page.url})")
                
                await page.wait_for_load_state("networkidle", timeout=5000)
                
                key_found = await DeltaResolver._find_key_on_page(page)
                if key_found:
                    return True, key_found

                page_type = await PageHandlers.detect_page_type(page)
                
                if page_type in ("captcha", "login_required"):
                    _, err_msg = await PageHandlers.handle_page(page, page_type)
                    return False, err_msg

                success, action_msg = await PageHandlers.handle_page(page, page_type)
                if not success:
                    return False, action_msg

                await asyncio.sleep(3)

            return False, "Đã vượt quá giới hạn số bước cho phép mà không tìm thấy KEY."

        except Exception as e:
            return False, f"Lỗi trong quá trình xử lý: {str(e)}"
        finally:
            await page.close()

    @staticmethod
    async def _find_key_on_page(page) -> str | None:
        try:
            selectors = ["code", "#key", ".key", "[id*='key']", "[class*='key']", "input[readonly]"]
            for sel in selectors:
                elements = await page.locator(sel).all()
                for el in elements:
                    if await el.is_visible():
                        text = await el.text_content() or await el.get_attribute("value")
                        if text:
                            text = text.strip()
                            if len(text) >= 16 and " " not in text and not text.lower().startswith("http"):
                                return text
        except Exception:
            pass
        return None

# ==================== DISCORD BOT SETUP ====================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

class KeyView(discord.ui.View):
    def __init__(self, key_text: str):
        super().__init__(timeout=180)
        self.key_text = key_text

    @discord.ui.button(label="📋 Copy Key", style=discord.ButtonStyle.green)
    async def copy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🔑 **KEY của bạn:**\n```{self.key_text}```", ephemeral=True
        )

@bot.event
async def on_ready():
    print(f"Bot đã đăng nhập thành công dưới tên: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Đã đồng bộ {len(synced)} lệnh slash.")
    except Exception as e:
        print(f"Lỗi đồng bộ lệnh: {e}")

@bot.tree.command(name="bypass", description="Tự động xử lý link Delta và lấy KEY cuối cùng.")
@app_commands.describe(link="Đường dẫn (URL) Delta cần lấy key")
async def bypass(interaction: discord.Interaction, link: str):
    if ALLOWED_CHANNEL_IDS and interaction.channel_id not in ALLOWED_CHANNEL_IDS:
        await interaction.response.send_message("❌ Lệnh này không được phép sử dụng trong kênh này!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🔍 Đang phân tích link...",
        description=f"Đang tiến hành xử lý đường dẫn:\n`{link}`",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()

    async def update_status(status_text: str):
        try:
            current_embed = message.embeds[0]
            current_embed.description = f"{status_text}\n\n`{link}`"
            await message.edit(embed=current_embed)
        except Exception:
            pass

    success, result = await DeltaResolver.resolve(link, update_status)

    if success:
        success_embed = discord.Embed(
            title="✅ DELTA KEY FOUND",
            description="Đã lấy thành công KEY từ trang đích:",
            color=discord.Color.green()
        )
        success_embed.add_field(name="KEY", value=f"```{result}```", inline=False)
        view = KeyView(result)
        await message.edit(embed=success_embed, view=view)
    else:
        error_embed = discord.Embed(
            title="❌ Không thể tiếp tục",
            description=f"**Nguyên nhân:** {result}",
            color=discord.Color.red()
        )
        await message.edit(embed=error_embed, view=None)

if __name__ == "__main__":
    if DISCORD_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("Vui lòng thay thế 'YOUR_DISCORD_BOT_TOKEN_HERE' bằng token thực tế của bạn trong file bot.py!")
    else:
        bot.run(DISCORD_TOKEN)