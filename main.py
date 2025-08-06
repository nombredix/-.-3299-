# Supprimer la sauvegarde après restauration
        del self.saved_roles[member.id]
        return True

    async def apply_sanction(self, ctx, member, sanction_role_id, action_name):
        """Applique une sanction (mute ou prison) à un membre"""
        try:
            guild = ctx.guild
            sanction_role = guild.get_role(sanction_role_id)
            
            if not sanction_role:
                await ctx.send(f"❌ Erreur: Rôle de {action_name} non trouvé dans la configuration.")
                return False
            
            # Vérifier si le membre a déjà ce rôle
            if sanction_role in member.roles:
                await ctx.send(f"⚠️ {member.mention} possède déjà le rôle {sanction_role.name}.")
                return False
            
            # Sauvegarder les rôles actuels
            await self.save_user_roles(member)
            
            # Supprimer tous les rôles sauf @everyone
            roles_to_remove = [role for role in member.roles if role.id != guild.default_role.id]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason=f"{action_name} par {ctx.author}")
            
            # Ajouter le rôle de sanction
            await member.add_roles(sanction_role, reason=f"{action_name} par {ctx.author}")
            
            # Message de confirmation
            await ctx.send(f"🔒 {member.mention} a été {action_name.lower()}(e) avec succès!")
            
            # Log de l'action
            await self.log_action(
                f"{action_name} appliqué(e)",
                ctx.author,
                member,
                sanction_role
            )
            
            logger.info(f"{member.display_name} {action_name.lower()}(e) par {ctx.author.display_name}")
            return True
            
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas les permissions nécessaires pour gérer les rôles de ce membre.")
            logger.error(f"Permissions insuffisantes pour {action_name.lower()} {member.display_name}")
            return False
            
        except Exception as e:
            await ctx.send(f"❌ Une erreur s'est produite lors de l'application de la sanction: {str(e)}")
            logger.error(f"Erreur lors de l'application de la sanction à {member.display_name}: {e}")
            return False

# Initialisation de la classe de vérification
verification_bot = VerificationBot(bot)

@bot.event
async def on_ready():
    """Événement déclenché quand le bot est prêt"""
    logger.info(f'{bot.user} est connecté et prêt!')
    
    # Vérifier la configuration
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        logger.error(f"Serveur Discord (ID: {GUILD_ID}) non trouvé")
        return
        
    missing_roles = []
    if not guild.get_role(TEMP_ROLE_ID):
        missing_roles.append(f"Rôle temporaire (ID: {TEMP_ROLE_ID})")
    if not guild.get_role(MEN_ROLE_ID):
        missing_roles.append(f"Rôle hommes (ID: {MEN_ROLE_ID})")
    if not guild.get_role(WOMEN_ROLE_ID):
        missing_roles.append(f"Rôle femmes (ID: {WOMEN_ROLE_ID})")
        
    if missing_roles:
        logger.warning(f"Rôles manquants: {', '.join(missing_roles)}")
        
    if not bot.get_channel(LOG_CHANNEL_ID):
        logger.warning(f"Canal de logs (ID: {LOG_CHANNEL_ID}) non trouvé")

@bot.event
async def on_member_join(member):
    """Événement déclenché quand un nouveau membre rejoint le serveur"""
    logger.info(f"Nouveau membre: {member.display_name} ({member.id})")
    
    # Vérifier que c'est le bon serveur
    if member.guild.id != GUILD_ID:
        return
        
    # Attendre un court délai pour s'assurer que le membre est complètement chargé
    await asyncio.sleep(1)
    
    # Attribuer le rôle temporaire
    await verification_bot.assign_temp_role(member)

def is_admin():
    """Décorateur pour vérifier les permissions d'administrateur"""
    async def predicate(ctx):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Cette commande est réservée aux administrateurs.")
            logger.warning(f"{ctx.author.display_name} a tenté d'utiliser une commande admin sans permissions")
            return False
        return True
    return commands.check(predicate)

@bot.command(name='men')
@is_admin()
async def verify_men(ctx, member: discord.Member = None):
    """Commande pour vérifier un membre masculin"""
    # Si aucun membre mentionné, vérifier si c'est une réponse à un message
    if member is None and ctx.message.reference:
        try:
            # Récupérer le message auquel on répond
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = replied_message.author
            # Vérifier que c'est bien un membre du serveur (pas un bot externe)
            if not isinstance(member, discord.Member):
                member = ctx.guild.get_member(member.id)
        except:
            pass
    
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre ou répondre à son message. Utilisation: `+men @membre` ou répondre à un message avec `+men`")
        return
        
    await verification_bot.verify_member(ctx, member, MEN_ROLE_ID)

@bot.command(name='wom')
@is_admin()
async def verify_women(ctx, member: discord.Member = None):
    """Commande pour vérifier un membre féminin"""
    # Si aucun membre mentionné, vérifier si c'est une réponse à un message
    if member is None and ctx.message.reference:
        try:
            # Récupérer le message auquel on répond
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = replied_message.author
            # Vérifier que c'est bien un membre du serveur (pas un bot externe)
            if not isinstance(member, discord.Member):
                member = ctx.guild.get_member(member.id)
        except:
            pass
    
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre ou répondre à son message. Utilisation: `+wom @membre` ou répondre à un message avec `+wom`")
        return
        
    await verification_bot.verify_member(ctx, member, WOMEN_ROLE_ID)

@bot.command(name='mute')
@is_admin()
async def mute_member(ctx, member: discord.Member = None, *, reason="Aucune raison spécifiée"):
    """Commande pour muter un membre"""
    # Gestion des réponses comme pour les autres commandes
    if member is None and ctx.message.reference:
        try:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = replied_message.author
            if not isinstance(member, discord.Member):
                member = ctx.guild.get_member(member.id)
        except:
            pass
    
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre ou répondre à son message. Utilisation: `+mute @membre [raison]`")
        return
    
    await verification_bot.apply_sanction(ctx, member, MUTE_ROLE_ID, "Mute")

@bot.command(name='hebs')
@is_admin()
async def prison_member(ctx, member: discord.Member = None, *, reason="Aucune raison spécifiée"):
    """Commande pour envoyer un membre en prison"""
    # Gestion des réponses comme pour les autres commandes
    if member is None and ctx.message.reference:
        try:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = replied_message.author
            if not isinstance(member, discord.Member):
                member = ctx.guild.get_member(member.id)
        except:
            pass
    
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre ou répondre à son message. Utilisation: `+hebs @membre [raison]`")
        return
    
    await verification_bot.apply_sanction(ctx, member, PRISON_ROLE_ID, "Prison")

@bot.command(name='unhebs')
@is_admin()
async def unprison_member(ctx, member: discord.Member = None):
    """Commande pour libérer un membre de prison"""
    # Gestion des réponses comme pour les autres commandes
    if member is None and ctx.message.reference:
        try:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = replied_message.author
            if not isinstance(member, discord.Member):
                member = ctx.guild.get_member(member.id)
        except:
            pass
    
    if member is None:
        await ctx.send("❌ Veuillez mentionner un membre ou répondre à son message. Utilisation: `+unhebs @membre`")
        return
    
    try:
        guild = ctx.guild
        prison_role = guild.get_role(PRISON_ROLE_ID)
        mute_role = guild.get_role(MUTE_ROLE_ID)
        
        # Vérifier si le membre est en prison ou muté
        if not (prison_role in member.roles or mute_role in member.roles):
            await ctx.send(f"⚠️ {member.mention} n'est pas en prison ou muté.")
            return
        
        # Supprimer les rôles de sanction
        roles_to_remove = []
        if prison_role in member.roles:
            roles_to_remove.append(prison_role)
        if mute_role in member.roles:
            roles_to_remove.append(mute_role)
        
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=f"Libération par {ctx.author}")
        
        # Restaurer les rôles sauvegardés
        restored = await verification_bot.restore_user_roles(member)
        
        if restored:
            await ctx.send(f"🔓 {member.mention} a été libéré(e) et ses rôles ont été restaurés!")
        else:
            await ctx.send(f"🔓 {member.mention} a été libéré(e) mais aucun rôle sauvegardé trouvé.")
        
        # Log de l'action
        await verification_bot.log_action(
            "Libération de prison/mute",
            ctx.author,
            member
        )
        
        logger.info(f"{member.display_name} libéré(e) par {ctx.author.display_name}")
        
    except discord.Forbidden:
        await ctx.send("❌ Je n'ai pas les permissions nécessaires pour gérer les rôles de ce membre.")
        logger.error(f"Permissions insuffisantes pour libérer {member.display_name}")
        
    except Exception as e:
        await ctx.send(f"❌ Une erreur s'est produite lors de la libération: {str(e)}")
        logger.error(f"Erreur lors de la libération de {member.display_name}: {e}")

@bot.command(name='omar')
async def omar_command(ctx):
    """Commande Omar - Envoie la vidéo spéciale"""
    try:
        # Vérifier si le fichier existe
        video_path = "omar_video.mov"
        if not os.path.exists(video_path):
            await ctx.send("❌ Fichier vidéo Omar non trouvé.")
            logger.error("Fichier omar_video.mov non trouvé")
            return
        
        # Envoyer la vidéo
        with open(video_path, 'rb') as video_file:
            await ctx.send("🎬 Omar !", file=discord.File(video_file, filename="omar.mov"))
        
        logger.info(f"Commande +omar exécutée par {ctx.author.display_name}")
        
    except Exception as e:
        await ctx.send("❌ Erreur lors de l'envoi de la vidéo Omar.")
        logger.error(f"Erreur lors de l'exécution de la commande +omar: {e}")

@bot.command(name='status')
@is_admin()
async def bot_status(ctx):
    """Affiche le statut du bot et sa configuration"""
    guild = ctx.guild
    
    embed = discord.Embed(
        title="📊 Statut du Bot de Vérification",
        color=0x0099ff,
        timestamp=datetime.utcnow()
    )
    
    # Vérifier les rôles
    temp_role = guild.get_role(TEMP_ROLE_ID)
    men_role = guild.get_role(MEN_ROLE_ID)
    women_role = guild.get_role(WOMEN_ROLE_ID)
    mute_role = guild.get_role(MUTE_ROLE_ID)
    prison_role = guild.get_role(PRISON_ROLE_ID)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    
    embed.add_field(
        name="🔧 Configuration",
        value=f"Rôle temporaire: {'✅' if temp_role else '❌'} {temp_role.name if temp_role else 'Non trouvé'}\n"
              f"Rôle hommes: {'✅' if men_role else '❌'} {men_role.name if men_role else 'Non trouvé'}\n"
              f"Rôle femmes: {'✅' if women_role else '❌'} {women_role.name if women_role else 'Non trouvé'}\n"
              f"Rôle mute: {'✅' if mute_role else '❌'} {mute_role.name if mute_role else 'Non trouvé'}\n"
              f"Rôle prison: {'✅' if prison_role else '❌'} {prison_role.name if prison_role else 'Non trouvé'}\n"
              f"Canal de logs: {'✅' if log_channel else '❌'} {log_channel.name if log_channel and hasattr(log_channel, 'name') else 'Non trouvé'}",
        inline=False
    )
    
    # Compter les membres avec différents rôles
    temp_members = len([m for m in guild.members if temp_role and temp_role in m.roles]) if temp_role else 0
    muted_members = len([m for m in guild.members if mute_role and mute_role in m.roles]) if mute_role else 0
    prison_members = len([m for m in guild.members if prison_role and prison_role in m.roles]) if prison_role else 0
    saved_roles_count = len(verification_bot.saved_roles)
    
    embed.add_field(
        name="📈 Statistiques",
        value=f"Membres en attente: {temp_members}\n"
              f"Membres mutés: {muted_members}\n"
              f"Membres en prison: {prison_members}\n"
              f"Rôles sauvegardés: {saved_roles_count}\n"
              f"Total membres: {guild.member_count}",
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.command(name='pending')
@is_admin()
async def list_pending_members(ctx):
    """Liste les membres en attente de vérification"""
    guild = ctx.guild
    temp_role = guild.get_role(TEMP_ROLE_ID)
    
    if not temp_role:
        await ctx.send("❌ Rôle temporaire non configuré.")
        return
        
    pending_members = [m for m in guild.members if temp_role in m.roles]
    
    if not pending_members:
        await ctx.send("✅ Aucun membre en attente de vérification.")
        return
        
    embed = discord.Embed(
        title="⏳ Membres en Attente de Vérification",
        color=0xffa500,
        timestamp=datetime.utcnow()
    )
    
    # Limiter l'affichage aux 25 premiers membres
    display_members = pending_members[:25]
    member_list = "\n".join([f"• {m.mention} - {m.display_name}" for m in display_members])
    
    embed.add_field(
        name=f"Membres ({len(pending_members)} total)",
        value=member_list,
        inline=False
    )
    
    if len(pending_members) > 25:
        embed.add_field(
            name="Note",
            value=f"Seuls les 25 premiers membres sont affichés. {len(pending_members) - 25} autres en attente.",
            inline=False
        )
        
    embed.add_field(
        name="Commandes",
        value="**Vérification:** `+men @membre` ou `+wom @membre`\n"
              "**Modération:** `+mute @membre` | `+hebs @membre` | `+unhebs @membre`\n"
              "**Info:** `+status` | `+pending`",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """Gestion des erreurs de commandes"""
    if isinstance(error, commands.CheckFailure):
        # Les erreurs de permissions sont déjà gérées dans le décorateur
        return
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Membre non trouvé. Assurez-vous de mentionner un membre valide.")
    elif isinstance(error, commands.CommandNotFound):
        # Ignorer les commandes non trouvées
        return
    else:
        logger.error(f"Erreur de commande: {error}")
        await ctx.send("❌ Une erreur inattendue s'est produite.")

@bot.event
async def on_error(event, *args, **kwargs):
    """Gestion des erreurs générales"""
    logger.error(f"Erreur dans l'événement {event}: {args}")

# Vérification de la configuration avant le démarrage
def check_configuration():
    """Vérifie que toutes les variables d'environnement nécessaires sont configurées"""
    required_vars = {
        'DISCORD_TOKEN': DISCORD_TOKEN,
        'TEMP_ROLE_ID': TEMP_ROLE_ID,
        'MEN_ROLE_ID': MEN_ROLE_ID,
        'WOMEN_ROLE_ID': WOMEN_ROLE_ID,
        'MUTE_ROLE_ID': MUTE_ROLE_ID,
        'PRISON_ROLE_ID': PRISON_ROLE_ID,
        'LOG_CHANNEL_ID': LOG_CHANNEL_ID,
        'GUILD_ID': GUILD_ID
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if not var_value or var_value == 0:
            missing_vars.append(var_name)
    
    if missing_vars:
        logger.error(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
        print("❌ Configuration incomplète!")
        print("Variables manquantes:", ', '.join(missing_vars))
        print("Veuillez configurer le fichier .env selon l'exemple fourni.")
        return False
    
    return True

if __name__ == "__main__":
    if not check_configuration():
        exit(1)
        
    try:
        logger.info("Démarrage du bot de vérification Discord...")
        if DISCORD_TOKEN:
            bot.run(DISCORD_TOKEN)
        else:
            logger.error("Token Discord non configuré")
            print("❌ Token Discord non configuré")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot: {e}")
        print(f"❌ Erreur: {e}")
