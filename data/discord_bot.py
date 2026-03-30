"""
Bot Discord AUDIPER — Audina
Cria canais espelhando o Chat do dashboard e sincroniza mensagens.
"""
import discord
import asyncio
import psycopg
import json
import os

TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')
DB_URL = 'postgresql://postgres:audiper2026@localhost:5432/audiper'

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
client = discord.Client(intents=intents)

CHANNEL_MAP = {}  # canal_nome -> discord_channel_id

# Canais para criar
CANAIS_PUBLICOS = {
    'economia-brasil': 'Noticias economicas, PIB, Selic, cambio',
    'regulacoes-contabeis': 'NBC TAs, CPCs, resolucoes CFC, atualizacoes',
    'reforma-tributaria': 'IBS, CBS, Split Payment, prazos e impactos',
    'lgpd-seguranca': 'LGPD, ISO 27001, protecao de dados',
    'servicos-audiper': 'Nossos servicos, cases, diferenciais, novidades',
}

CANAIS_EQUIPE = {
    'geral': 'Comunicacao geral da equipe',
    'oig-gaming': 'Auditoria OIG Gaming 2025',
    'unimed-floriano': 'Auditoria Unimed Floriano 2025',
    'fapec': 'Auditoria FAPEC 2025',
    'megalink': 'Auditoria Megalink Telecom 2025',
    'leads': 'Pipeline de leads qualificados',
    'artigos': 'Rascunhos de artigos para o blog',
    'resumo-diario': 'Resumo consolidado do dia',
}

async def setup_server(guild):
    """Cria categorias e canais no servidor."""
    print(f"Configurando servidor: {guild.name} ({guild.id})")

    # Apagar canais antigos que nao sao uteis
    canais_manter = set(list(CANAIS_PUBLICOS.keys()) + list(CANAIS_EQUIPE.keys()))
    for ch in guild.text_channels:
        if ch.name not in canais_manter:
            try:
                await ch.delete(reason="Reorganizacao AUDIPER")
                print(f"  Canal antigo removido: #{ch.name}")
            except:
                pass

    # Criar categorias
    cat_publico = discord.utils.get(guild.categories, name='AUDIPER Publico')
    if not cat_publico:
        cat_publico = await guild.create_category('AUDIPER Publico')
        print(f"  Categoria criada: AUDIPER Publico")

    cat_equipe = discord.utils.get(guild.categories, name='Equipe Auditoria')
    if not cat_equipe:
        # Permissoes: so membros com role "Auditor" veem
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        cat_equipe = await guild.create_category('Equipe Auditoria', overwrites=overwrites)
        print(f"  Categoria criada: Equipe Auditoria (privada)")

    # Criar canais publicos
    for nome, desc in CANAIS_PUBLICOS.items():
        existing = discord.utils.get(guild.text_channels, name=nome)
        if not existing:
            ch = await guild.create_text_channel(nome, category=cat_publico, topic=desc)
            print(f"  Canal publico criado: #{nome}")
            CHANNEL_MAP[nome] = ch.id
        else:
            CHANNEL_MAP[nome] = existing.id

    # Criar canais da equipe
    for nome, desc in CANAIS_EQUIPE.items():
        existing = discord.utils.get(guild.text_channels, name=nome)
        if not existing:
            ch = await guild.create_text_channel(nome, category=cat_equipe, topic=desc)
            print(f"  Canal equipe criado: #{nome}")
            CHANNEL_MAP[nome] = ch.id
        else:
            CHANNEL_MAP[nome] = existing.id

    print(f"  {len(CHANNEL_MAP)} canais configurados")

    # Mensagem de boas-vindas no #geral
    geral_ch = discord.utils.get(guild.text_channels, name='geral')
    if geral_ch:
        embed = discord.Embed(
            title="Audina — Assistente de Auditoria AUDIPER",
            description="Sistema de comunicacao da equipe de auditoria ativo.\n\n"
                       "**Canais publicos:** economia, regulacoes, reforma tributaria, LGPD, servicos\n"
                       "**Canais equipe:** auditorias individuais, leads, artigos, resumo diario\n\n"
                       "Mensagens sao sincronizadas com o Dashboard AUDIPER.",
            color=0xE72C22
        )
        embed.set_footer(text="AUDIPER — 40 anos de tradicao aliada a inovacao")
        await geral_ch.send(embed=embed)

@client.event
async def on_ready():
    print(f"Audina conectada como {client.user}")
    for guild in client.guilds:
        await setup_server(guild)
    print("Setup completo! Bot ativo.")

    # Iniciar sincronizacao
    client.loop.create_task(sync_from_db())

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Salvar mensagem no PostgreSQL (espelhamento Discord -> Dashboard)
    canal_nome = message.channel.name
    autor = message.author.display_name
    texto = message.content

    if texto and canal_nome in {**CANAIS_PUBLICOS, **CANAIS_EQUIPE}:
        try:
            conn = psycopg.connect(DB_URL, autocommit=True)
            conn.execute(
                "INSERT INTO chat_mensagens (canal, autor, tipo, mensagem) VALUES (%s, %s, 'humano', %s)",
                (canal_nome, autor, texto)
            )
            conn.close()
        except Exception as e:
            print(f"Erro salvando no DB: {e}")

async def sync_from_db():
    """Sincroniza mensagens do Dashboard -> Discord a cada 30s."""
    await client.wait_until_ready()
    last_id = 0

    # Pegar ultimo ID
    try:
        conn = psycopg.connect(DB_URL, autocommit=True)
        row = conn.execute("SELECT MAX(id) FROM chat_mensagens").fetchone()
        if row and row[0]:
            last_id = row[0]
        conn.close()
    except:
        pass

    while not client.is_closed():
        try:
            conn = psycopg.connect(DB_URL, autocommit=True)
            rows = conn.execute(
                "SELECT id, canal, autor, tipo, mensagem FROM chat_mensagens WHERE id > %s AND tipo = 'agente' ORDER BY id",
                (last_id,)
            ).fetchall()
            conn.close()

            for row in rows:
                msg_id, canal, autor, tipo, mensagem = row
                last_id = msg_id

                # Encontrar canal Discord
                for guild in client.guilds:
                    ch = discord.utils.get(guild.text_channels, name=canal)
                    if ch:
                        embed = discord.Embed(
                            description=mensagem[:2000],
                            color=0x3B82F6  # Azul para agentes
                        )
                        embed.set_author(name=f"{autor} (IA)")
                        await ch.send(embed=embed)
                        break

        except Exception as e:
            print(f"Sync error: {e}")

        await asyncio.sleep(30)

if __name__ == '__main__':
    print("Iniciando Audina Discord Bot...")
    client.run(TOKEN)
