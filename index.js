const { Client, GatewayIntentBits } = require('discord.js');
const axios = require('axios');

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ]
});

const BOT_TOKEN = process.env.BOT_TOKEN; 

client.once('ready', () => {
    console.log(`[HỆ THỐNG] Bot đã sẵn sàng: ${client.user.tag}`);
});

client.on('messageCreate', async (message) => {
    if (message.author.bot) return;

    if (message.content.includes('platoboost.com') || message.content.includes('linkvertise.com')) {
        
        const urlMatch = message.content.match(/(https?:\/\/[^\s]+)/);
        if (!urlMatch) return;
        
        const targetUrl = urlMatch[0];
        const waitingMessage = await message.reply('⏳ Đang tiến hành vượt link Delta, vui lòng chờ...');

        try {
            const response = await axios.get(`https://bypass.vip/api/bypass?url=${encodeURIComponent(targetUrl)}`);
            
            if (response.data && response.data.result) {
                const bypassedUrl = response.data.result;
                await waitingMessage.edit(`✅ **Vượt Link Delta Thành Công!**\n🔗 **Link Gốc:** <${targetUrl}>\n🚀 **Kết Quả Key/Link:** ${bypassedUrl}`);
            } else {
                await waitingMessage.edit('❌ Hệ thống không trả về kết quả. Link có thể đã hết hạn hoặc sai cấu trúc.');
            }
        } catch (error) {
            console.error('Lỗi API:', error.message);
            await waitingMessage.edit('❌ Hệ thống API Bypass đang gặp lỗi hoặc quá tải. Vui lòng thử lại sau.');
        }
    }
});

client.login(BOT_TOKEN);