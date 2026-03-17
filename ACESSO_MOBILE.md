# 📱 Guia de Acesso Mobile - Liga YGO Marabá

## 🔍 **Informações da sua rede**
- **IP do computador:** `192.168.0.8`
- **Porta da aplicação:** `5000`
- **URL para celular:** `http://192.168.0.8:5000`

## 📱 **Como acessar pelo celular**

### **Passo 1: Conectar na mesma rede WiFi**
- Certifique-se que o celular está na **mesma rede WiFi** que o computador
- Ambos devem estar conectados no mesmo roteador/WiFi

### **Passo 2: Iniciar a aplicação no computador**
```bash
# Execute um destes comandos no computador:
python app.py
# OU
run.bat
# OU
run.ps1
```

### **Passo 3: Acessar no celular**
1. Abra o navegador do celular (Chrome, Safari, etc.)
2. Digite na barra de endereço:
   ```
   http://192.168.0.8:5000
   ```
3. Pressione Enter

## ✅ **Teste se está funcionando**
- A página inicial do Liga YGO Marabá deve aparecer no celular
- Você verá os botões: Cadastrar Torneio, Cadastrar Pontos, etc.
- A interface será responsiva e se adaptará ao tamanho do celular

## 🚨 **Se não funcionar**

### **Problema 1: "Site não pode ser acessado"**
**Solução:** Liberar porta no Windows Firewall

1. Abra o PowerShell como Administrador
2. Execute o comando:
```powershell
New-NetFirewallRule -DisplayName "Flask App Port 5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

### **Problema 2: "Conexão recusada"**
**Verificar:**
- ✅ Celular na mesma WiFi que o computador
- ✅ Aplicação Flask rodando no computador
- ✅ IP correto (192.168.0.8)

### **Problema 3: IP mudou**
Se o IP do computador mudou, descobrir o novo:
```cmd
ipconfig | findstr "IPv4"
```

## 🌐 **URLs Alternativas para testar**

Se `192.168.0.8:5000` não funcionar, tente:
- `http://192.168.1.8:5000` (rede diferente)
- `http://10.0.0.8:5000` (algumas redes corporativas)

## 📋 **Funcionalidades no celular**

Todas as funcionalidades funcionam no celular:
- ✅ Cadastrar Torneio
- ✅ Cadastrar Pontos
- ✅ Buscar Duelista
- ✅ Ver Ranking
- ✅ Alterar Duelista
- ✅ Navegação responsiva
- ✅ Formulários otimizados para touch

## 🎯 **Dicas de uso mobile**

1. **Adicionar à tela inicial:**
   - Chrome: Menu → "Adicionar à tela inicial"
   - Safari: Compartilhar → "Adicionar à Tela de Início"

2. **Melhor orientação:**
   - Portrait (vertical) para formulários
   - Landscape (horizontal) para tabelas/ranking

3. **Atalhos touch:**
   - Toque duplo para zoom
   - Deslizar para navegar em tabelas
   - Toque longo para opções de contexto

## 🔧 **Para desenvolvedores**

### **Configuração atual do Flask:**
```python
# Em app.py, linha final:
app.run(debug=True, host='0.0.0.0', port=5000)
```

- `host='0.0.0.0'`: Aceita conexões de qualquer IP
- `port=5000`: Porta padrão
- `debug=True`: Modo desenvolvimento (recarregamento automático)

### **Para usar porta diferente:**
```python
app.run(debug=True, host='0.0.0.0', port=8080)
# URL ficaria: http://192.168.0.8:8080
```

### **Para produção (mais seguro):**
```python
app.run(debug=False, host='192.168.0.8', port=5000)
```

## 📞 **Suporte**

Se ainda tiver problemas:
1. Verifique se ambos dispositivos estão na mesma rede
2. Teste abrir http://192.168.0.8:5000 no computador primeiro
3. Desative temporariamente firewall/antivírus
4. Reinicie a aplicação Flask
5. Verifique se não há outro programa usando a porta 5000

---

**Aproveite o sistema Liga YGO Marabá no seu celular! 🏆📱**