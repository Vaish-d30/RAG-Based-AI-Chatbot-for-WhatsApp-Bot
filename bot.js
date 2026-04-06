const { Client } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

const client = new Client();

client.on('qr', qr => {
    console.log('Scan this QR code:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('WhatsApp Bot is READY 🚀');
});

// ✅ Message handler using FastAPI
client.on('message', async (message) => {
    const user_id = message.from;
    const user_msg = message.body;

    console.log(`User: ${user_msg}`);

    try {
        // 🔥 Call FastAPI backend
        const res = await axios.post('http://localhost:8000/chat', {
            user_id: user_id,
            message: user_msg
        });

        const botReply = res.data.response;

        if (botReply && botReply.trim()) {
            message.reply(botReply);
        } else {
            message.reply("⚠️ Empty response from server");
        }

    } catch (err) {
        console.error("API Error:", err.message);

        if (err.response) {
            console.error("Server response:", err.response.data);
        }

        message.reply("⚠️ Server error. Try again later.");
    }
});

client.initialize();