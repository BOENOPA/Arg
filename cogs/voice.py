import asyncio
import traceback

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓN
# ============================================================

RECONNECT_MIN = 5
RECONNECT_MAX = 60


# ============================================================
# VOICE COG
# ============================================================

class Voice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # guild_id -> canal de voz objetivo
        self.voice_channels: dict[int, int] = {}

        # guild_id -> tarea de reconexión
        self.reconnect_tasks: dict[int, asyncio.Task] = {}

        # guild_id -> lock para evitar conexiones simultáneas
        self.voice_locks: dict[int, asyncio.Lock] = {}

        print("[VOICE] Cog cargado correctamente.")

    # ========================================================
    # LOCK
    # ========================================================

    def get_lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self.voice_locks:
            self.voice_locks[guild_id] = asyncio.Lock()

        return self.voice_locks[guild_id]

    # ========================================================
    # /vc
    # ========================================================

    @app_commands.command(
        name="vc",
        description="Hace que el bot entre a tu canal de voz."
    )
    async def vc(self, interaction: discord.Interaction):

        print(
            f"[VOICE] /vc ejecutado por "
            f"{interaction.user} ({interaction.user.id})"
        )

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse dentro de un servidor.",
                ephemeral=True
            )
            return

        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "❌ No pude obtener tu información de miembro.",
                ephemeral=True
            )
            return

        if interaction.user.voice is None:
            print("[VOICE] ❌ El usuario no está en un canal de voz.")

            await interaction.response.send_message(
                "❌ Tenés que estar conectado a un canal de voz.",
                ephemeral=True
            )
            return

        canal = interaction.user.voice.channel

        if not isinstance(
            canal,
            (
                discord.VoiceChannel,
                discord.StageChannel
            )
        ):
            await interaction.response.send_message(
                "❌ Ese canal no es compatible.",
                ephemeral=True
            )
            return

        guild_id = interaction.guild.id

        print(
            f"[VOICE] Canal solicitado: "
            f"{canal.name} ({canal.id})"
        )

        await interaction.response.defer(ephemeral=True)

        lock = self.get_lock(guild_id)

        async with lock:

            # Guardamos SIEMPRE el canal deseado
            self.voice_channels[guild_id] = canal.id

            # Cancelamos una reconexión anterior
            task = self.reconnect_tasks.get(guild_id)

            if task is not None and not task.done():
                task.cancel()
                self.reconnect_tasks.pop(guild_id, None)

            voice_client = interaction.guild.voice_client

            try:

                # ====================================================
                # YA ESTÁ CONECTADO
                # ====================================================

                if voice_client is not None and voice_client.is_connected():

                    print(
                        "[VOICE] ✅ El bot ya está conectado a voz."
                    )

                    if voice_client.channel != canal:

                        print(
                            f"[VOICE] 🔄 Moviendo bot de "
                            f"{voice_client.channel} → {canal}"
                        )

                        await voice_client.move_to(canal)

                    # Aseguramos mute + deaf
                    try:
                        await interaction.guild.change_voice_state(
                            channel=canal,
                            self_mute=True,
                            self_deaf=True
                        )

                        print(
                            "[VOICE] 🔇 Mute + deaf aplicados."
                        )

                    except Exception as e:
                        print(
                            f"[VOICE] ⚠️ No se pudo actualizar "
                            f"mute/deaf: {e}"
                        )

                    await interaction.followup.send(
                        f"🔊 Ya estoy conectado en {canal.mention}.",
                        ephemeral=True
                    )

                    return

                # ====================================================
                # CLIENTE VIEJO / ROTO
                # ====================================================

                if voice_client is not None:

                    print(
                        "[VOICE] ⚠️ Encontré una conexión vieja. "
                        "Desconectando..."
                    )

                    try:
                        await voice_client.disconnect(
                            force=True
                        )
                    except Exception:
                        pass

                    await asyncio.sleep(1)

                # ====================================================
                # CONECTAR
                # ====================================================

                print(
                    f"[VOICE] 🔌 Conectando a {canal.name}..."
                )

                nuevo_cliente = await canal.connect(
                    timeout=45,
                    reconnect=True,
                    self_deaf=True,
                    self_mute=True
                )

                # ====================================================
                # FORZAR MUTE / DEAF
                # ====================================================

                try:

                    await interaction.guild.change_voice_state(
                        channel=canal,
                        self_mute=True,
                        self_deaf=True
                    )

                except Exception as e:

                    print(
                        f"[VOICE] ⚠️ Error aplicando "
                        f"mute/deaf: {e}"
                    )

                # ====================================================
                # COMPROBAR
                # ====================================================

                if nuevo_cliente.is_connected():

                    print(
                        f"[VOICE] ✅ CONECTADO correctamente "
                        f"en {canal.name}"
                    )

                    print(
                        "[VOICE] 🔇 Estado: MUTE + DEAF"
                    )

                    await interaction.followup.send(
                        f"🔊 Me conecté a {canal.mention} "
                        f"y quedé muteado.",
                        ephemeral=True
                    )

                else:

                    print(
                        "[VOICE] ❌ connect() terminó pero "
                        "el cliente no está conectado."
                    )

                    await interaction.followup.send(
                        "❌ No pude completar la conexión de voz.",
                        ephemeral=True
                    )

                    self.start_reconnect(guild_id)

            except asyncio.TimeoutError:

                print(
                    "[VOICE] ❌ Timeout conectando a voz."
                )

                await interaction.followup.send(
                    "❌ Discord tardó demasiado en conectar "
                    "la conexión de voz.",
                    ephemeral=True
                )

                self.start_reconnect(guild_id)

            except discord.ClientException as e:

                print(
                    f"[VOICE] ❌ ClientException: {e}"
                )

                await interaction.followup.send(
                    f"❌ Error de conexión: `{e}`",
                    ephemeral=True
                )

                self.start_reconnect(guild_id)

            except Exception as e:

                print(
                    f"[VOICE] ❌ Error inesperado: {e}"
                )

                traceback.print_exc()

                await interaction.followup.send(
                    "❌ Ocurrió un error intentando conectarme.",
                    ephemeral=True
                )

                self.start_reconnect(guild_id)

    # ========================================================
    # /vcsalir
    # ========================================================

    @app_commands.command(
        name="vcsalir",
        description="Hace que el bot salga del canal de voz."
    )
    async def vcsalir(self, interaction: discord.Interaction):

        print(
            f"[VOICE] /vcsalir ejecutado por "
            f"{interaction.user} ({interaction.user.id})"
        )

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse dentro de un servidor.",
                ephemeral=True
            )
            return

        guild_id = interaction.guild.id

        # ====================================================
        # CANCELAR RECONEXIÓN
        # ====================================================

        task = self.reconnect_tasks.get(guild_id)

        if task is not None and not task.done():

            print(
                "[VOICE] 🛑 Cancelando reconexión automática."
            )

            task.cancel()

        self.reconnect_tasks.pop(guild_id, None)

        # ====================================================
        # BORRAR CANAL OBJETIVO
        # ====================================================

        self.voice_channels.pop(guild_id, None)

        # ====================================================
        # DESCONECTAR
        # ====================================================

        voice_client = interaction.guild.voice_client

        if voice_client is None:

            print(
                "[VOICE] ⚠️ El bot no está conectado a voz."
            )

            await interaction.response.send_message(
                "❌ No estoy conectado a ningún canal de voz.",
                ephemeral=True
            )

            return

        try:

            if voice_client.is_connected():

                canal = voice_client.channel

                print(
                    f"[VOICE] 🔌 Saliendo de "
                    f"{canal.name if canal else 'voz'}..."
                )

                await voice_client.disconnect(
                    force=True
                )

            else:

                try:
                    await voice_client.disconnect(
                        force=True
                    )
                except Exception:
                    pass

            print(
                "[VOICE] ✅ Bot desconectado correctamente."
            )

            await interaction.response.send_message(
                "👋 Salí del canal de voz.",
                ephemeral=True
            )

        except Exception as e:

            print(
                f"[VOICE] ❌ Error al desconectar: {e}"
            )

            await interaction.response.send_message(
                "❌ No pude salir correctamente del canal.",
                ephemeral=True
            )

    # ========================================================
    # INICIAR RECONEXIÓN
    # ========================================================

    def start_reconnect(self, guild_id: int):

        existing = self.reconnect_tasks.get(guild_id)

        if existing is not None and not existing.done():
            return

        print(
            f"[VOICE] 🔄 Programando reconexión "
            f"para guild {guild_id}"
        )

        task = asyncio.create_task(
            self.reconnect_voice(guild_id)
        )

        self.reconnect_tasks[guild_id] = task

    # ========================================================
    # RECONEXIÓN AUTOMÁTICA
    # ========================================================

    async def reconnect_voice(self, guild_id: int):

        attempt = 0

        try:

            while guild_id in self.voice_channels:

                guild = self.bot.get_guild(guild_id)

                if guild is None:

                    print(
                        "[VOICE] ❌ Guild no encontrada."
                    )

                    return

                channel_id = self.voice_channels.get(
                    guild_id
                )

                if channel_id is None:
                    return

                channel = guild.get_channel(channel_id)

                if channel is None:

                    print(
                        "[VOICE] ❌ Canal de voz no encontrado."
                    )

                    return

                # ====================================================
                # SI YA ESTÁ CONECTADO
                # ====================================================

                voice_client = guild.voice_client

                if (
                    voice_client is not None
                    and voice_client.is_connected()
                ):

                    print(
                        "[VOICE] ✅ La conexión volvió "
                        "por sí sola."
                    )

                    try:

                        await guild.change_voice_state(
                            channel=channel,
                            self_mute=True,
                            self_deaf=True
                        )

                    except Exception:
                        pass

                    return

                attempt += 1

                wait_time = min(
                    RECONNECT_MIN * attempt,
                    RECONNECT_MAX
                )

                print(
                    f"[VOICE] 🔄 Intento de reconexión "
                    f"#{attempt} en {wait_time}s..."
                )

                await asyncio.sleep(wait_time)

                # ====================================================
                # EVITAR CONEXIONES DUPLICADAS
                # ====================================================

                lock = self.get_lock(guild_id)

                async with lock:

                    if guild_id not in self.voice_channels:
                        return

                    voice_client = guild.voice_client

                    if (
                        voice_client is not None
                        and voice_client.is_connected()
                    ):
                        return

                    try:

                        if voice_client is not None:

                            try:
                                await voice_client.disconnect(
                                    force=True
                                )
                            except Exception:
                                pass

                            await asyncio.sleep(1)

                        print(
                            f"[VOICE] 🔌 Reconectando a "
                            f"{channel.name}..."
                        )

                        nuevo_cliente = await channel.connect(
                            timeout=45,
                            reconnect=True,
                            self_deaf=True,
                            self_mute=True
                        )

                        try:

                            await guild.change_voice_state(
                                channel=channel,
                                self_mute=True,
                                self_deaf=True
                            )

                        except Exception:
                            pass

                        if nuevo_cliente.is_connected():

                            print(
                                "[VOICE] ✅ RECONEXIÓN EXITOSA."
                            )

                            print(
                                "[VOICE] 🔇 Mute + deaf activos."
                            )

                            return

                    except asyncio.CancelledError:

                        print(
                            "[VOICE] 🛑 Reconexión cancelada."
                        )

                        raise

                    except Exception as e:

                        print(
                            f"[VOICE] ❌ Falló reconexión: {e}"
                        )

                        traceback.print_exc()

        except asyncio.CancelledError:

            print(
                f"[VOICE] 🛑 Tarea de reconexión "
                f"cancelada para {guild_id}."
            )

        finally:

            current = self.reconnect_tasks.get(
                guild_id
            )

            if current is asyncio.current_task():

                self.reconnect_tasks.pop(
                    guild_id,
                    None
                )

    # ========================================================
    # CAMBIOS DE ESTADO DE VOZ
    # ========================================================

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):

        # Solo nos interesa nuestro propio bot
        if member.id != self.bot.user.id:
            return

        guild_id = member.guild.id

        target_channel_id = self.voice_channels.get(
            guild_id
        )

        if target_channel_id is None:
            return

        # ====================================================
        # BOT SE DESCONECTÓ
        # ====================================================

        if before.channel is not None and after.channel is None:

            print(
                f"[VOICE] ⚠️ El bot se desconectó de "
                f"{before.channel.name}."
            )

            print(
                "[VOICE] 🔄 Iniciando reconexión automática..."
            )

            self.start_reconnect(guild_id)

            return

        # ====================================================
        # BOT FUE MOVIDO
        # ====================================================

        if (
            after.channel is not None
            and after.channel.id != target_channel_id
        ):

            print(
                f"[VOICE] ⚠️ El bot fue movido a "
                f"{after.channel.name}."
            )

            self.voice_channels[guild_id] = (
                after.channel.id
            )

            return

        # ====================================================
        # SE CONECTÓ PERO NO ESTÁ MUTEADO/DEAF
        # ====================================================

        if after.channel is not None:

            if not after.self_mute or not after.self_deaf:

                print(
                    "[VOICE] 🔇 Reaplicando MUTE + DEAF..."
                )

                try:

                    await member.guild.change_voice_state(
                        channel=after.channel,
                        self_mute=True,
                        self_deaf=True
                    )

                except Exception as e:

                    print(
                        f"[VOICE] ⚠️ No se pudo "
                        f"reaplicar mute/deaf: {e}"
                    )

    # ========================================================
    # LIMPIEZA AL DESCARGAR COG
    # ========================================================

    def cog_unload(self):

        print("[VOICE] Descargando cog...")

        for task in self.reconnect_tasks.values():

            if not task.done():
                task.cancel()

        self.reconnect_tasks.clear()
        self.voice_channels.clear()
        self.voice_locks.clear()

        print("[VOICE] Cog descargado.")


# ============================================================
# SETUP
# ============================================================

async def setup(bot: commands.Bot):

    await bot.add_cog(
        Voice(bot)
    )

    print(
        "[VOICE] ✅ cogs.voice cargado correctamente."
    )