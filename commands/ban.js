module.exports = {
    name: 'ban',
    description: 'Bannit un utilisateur.',
    async execute(message, args) {
        if (!message.member.permissions.has('BAN_MEMBERS')) {
            return message.reply("❌ Tu n'as pas la permission de bannir.");
        }

        const userMention = message.mentions.users.first();
        if (!userMention) {
            return message.reply("❌ Mentionne un utilisateur à bannir.");
        }

        const member = await message.guild.members.fetch(userMention.id);
        await member.ban();

        message.channel.send(`✅ ${userMention.tag} a été banni.`);
    }
};
