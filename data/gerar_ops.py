import sqlite3, json

conn = sqlite3.connect("D:/Site/audiper/data/audiper.db")
c = conn.cursor()

data = {
    "sessoes": [dict(zip(["id","data","resumo","conquistas","horas","criado_em"], r))
        for r in c.execute("SELECT id,data,resumo,conquistas,horas_estimadas,criado_em FROM sessoes ORDER BY data DESC")],
    "pendencias": [dict(zip(["id","descricao","prioridade","area","status","criado_em"], r))
        for r in c.execute("SELECT id,descricao,prioridade,area,status,criado_em FROM pendencias ORDER BY CASE prioridade WHEN 'ALTA' THEN 1 WHEN 'MEDIA' THEN 2 ELSE 3 END")],
    "aprendizados": [dict(zip(["id","categoria","descricao","aplicado","criado_em"], r))
        for r in c.execute("SELECT id,categoria,descricao,aplicado,criado_em FROM aprendizados ORDER BY categoria")],
    "evolucao": [dict(zip(["data","metrica","valor","criado_em"], r))
        for r in c.execute("SELECT data,metrica,valor,criado_em FROM evolucao ORDER BY metrica")],
}
conn.close()

with open("D:/Site/audiper/data/ops-data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"ops-data.json gerado: {len(data['sessoes'])} sessoes, {len(data['pendencias'])} pendencias, {len(data['aprendizados'])} aprendizados")
