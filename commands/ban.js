module.exports = {
    name: 'ban',
    description: 'Bannit un membre mentionné ou un membre dont le message est répondu.',
    async execute(message, args) {
        if (!message.member.permissions.has('BanMembers')) {
            return message.reply("❌ Tu n'as pas la permission de bannir.");
        }

        const userMention = message.mentions.users.first();
        let userToBan;

        if (message.reference) {
            try {
                const repliedMessage = await message.channel.messages.fetch(message.reference.messageId);
                userToBan = repliedMessage.author;
            } catch (err) {
                return message.reply("❌ Impossible de récupérer le message répondu.");
            }
        } else if (userMention) {
            userToBan = userMention;
        } else {
            return message.reply("❌ Mentionne un utilisateur ou réponds à son message pour le bannir.");
        }

        try {
            const member = await message.guild.members.fetch(userToBan.id); // Fetch membre
            if (!member || !member.bannable) {
                return message.reply("❌ Je ne peux pas bannir cet utilisateur.");
            }

            const reason = args.slice(1).join(' ') || 'Aucune raison fournie.';
            await member.ban({ reason });
            message.channel.send(`✅ ${userToBan.tag} a été banni. Raison : ${reason}`);
        } catch (err) {
            console.error("Erreur lors du bannissement :", err);
            message.reply("❌ Une erreur est survenue pendant le bannissement.");
        }
    }
};
