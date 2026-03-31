# Como Escanear QR Codes no Sistema

## Para Produção - Leitor USB

### Configuração Inicial

1. Conectar leitor USB no computador
2. Windows instala driver automaticamente
3. Testar no Bloco de Notas:
   - Abrir Bloco de Notas
   - Apontar leitor para qualquer QR Code
   - Apertar gatilho
   - Texto deve aparecer digitado automaticamente

### Uso no Sistema

1. Operador abre sistema no navegador
2. Clica no campo de código da sacola
3. Aponta leitor para QR Code na sacola
4. Aperta gatilho
5. Sistema processa automaticamente

O leitor funciona como teclado - digita o conteúdo do QR Code no campo ativo.

---

## Para Testes - Remote Keyboard (Android)

### Configuração

1. Instalar app "Remote Keyboard" da Play Store
2. Conectar celular e PC na mesma rede WiFi
3. Abrir app e anotar IP mostrado
4. No PC, acessar o IP pelo navegador
5. Clicar em "Connect"

### Uso

1. Manter app conectado
2. No sistema, clicar no campo de código
3. No celular, apontar câmera para QR Code
4. App lê e digita automaticamente no PC

---

## Alternativa - Digitação Manual

Se leitor não estiver disponível ou QR Code danificado:

1. Abrir arquivo CSV do lote
2. Localizar código desejado na coluna `qr_content`
3. Copiar: `BAG-00001:2026-03-31:757314`
4. Colar no sistema

Ou digitar manualmente o código completo.

---

## Troubleshooting

**Leitor USB não funciona:**
- Verificar conexão USB
- Testar em outra porta USB
- Reiniciar computador

**Leitor digita caracteres errados:**
- Limpar lente do leitor
- Melhorar iluminação do ambiente
- Verificar se QR Code está danificado

**Remote Keyboard não conecta:**
- Confirmar que dispositivos estão na mesma rede WiFi
- Reiniciar app
- Verificar firewall do Windows