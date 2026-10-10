# Primeiro programa da PoC: a "impressão digital" (hash) e a corrente de eventos.
# É o coração do sistema (DA-27): cada evento guarda o hash do anterior.
# Dados 100% fictícios.

import hashlib  # biblioteca padrão do Python para calcular hashes
import json     # para transformar dados em texto padronizado


def impressao_digital(texto):
    """Calcula o hash SHA-256 de um texto e devolve os 64 caracteres."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# --- Parte 1: uma letra muda tudo ---------------------------------------
print("=== Parte 1: a impressão digital ===")
print("Hortolândia ->", impressao_digital("Hortolândia"))
print("Hortolandia ->", impressao_digital("Hortolandia"))
print("(só tiramos o acento do 'a' e o código mudou inteiro)\n")


# --- Parte 2: uma corrente de 3 eventos ---------------------------------
def selar(evento, hash_anterior):
    """Junta o evento com o hash do anterior e calcula o hash do conjunto."""
    pacote = dict(evento, hash_anterior=hash_anterior)
    # JSON "canônico": chaves em ordem fixa e sem espaços, para o hash ser sempre igual
    texto = json.dumps(pacote, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return impressao_digital(texto)


eventos = [
    {"seq": 1, "acao": "submeter", "pessoa": "Pessoa A (fictícia)", "registro": "REG-0001"},
    {"seq": 2, "acao": "analisar", "pessoa": "Pessoa B (fictícia)", "registro": "REG-0001"},
    {"seq": 3, "acao": "validar",  "pessoa": "Pessoa B (fictícia)", "registro": "REG-0001"},
]

print("=== Parte 2: a corrente ===")
corrente = []
anterior = "0" * 64  # o primeiro elo não tem anterior
for ev in eventos:
    h = selar(ev, anterior)
    corrente.append(h)
    print(f"evento {ev['seq']} ({ev['acao']}): {h[:16]}...")
    anterior = h


# --- Parte 3: alguém tenta adulterar o evento 2 -------------------------
def verificar(eventos, corrente):
    anterior = "0" * 64
    for ev, h_guardado in zip(eventos, corrente):
        if selar(ev, anterior) != h_guardado:
            return f"ADULTERAÇÃO DETECTADA no evento {ev['seq']}!"
        anterior = h_guardado
    return "Corrente íntegra: nada foi alterado."

print("\n=== Parte 3: a verificação ===")
print("Antes: ", verificar(eventos, corrente))
eventos[1]["acao"] = "devolver"   # adulteração: trocamos 'analisar' por 'devolver'
print("Depois:", verificar(eventos, corrente))
