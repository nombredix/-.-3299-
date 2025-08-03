module.exports = {
    name: 'kick',
    description: 'Expulse un utilisateur du serveur.',
    async execute(message, args) {
        if (!message.member.permissions.has('KICK_MEMBERS')) {
            return message.reply("❌ Tu n'as pas la permission de kicker des membres.");
        }

        const userMention = message.mentions.users.first();

        if (!userMention) {
            return message.reply("❌ Mentionne un utilisateur à expulser.");
        }

        const member = await message.guild.members.fetch(userMention.id);

        if (!member || !member.kickable) {
            return message.reply("❌ Je ne peux pas expulser cet utilisateur.");
        }

        const reason = args.slice(1).join(' ') || 'Aucune raison fournie.';
        await member.kick(reason);

        message.channel.send(`✅ ${userMention.tag} a été expulsé pour : ${reason}`);
    }
};
