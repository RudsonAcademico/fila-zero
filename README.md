# 📌 Fila Zero — Gestão de Agendamentos

Sistema web desenvolvido com Flask para gerenciamento de consultas, com autenticação de usuários, persistência em MongoDB e automação de tarefas em background.

---

## 🧰 Bibliotecas Utilizadas

**Flask**  
Framework web leve utilizado para criação de rotas, renderização de templates, gerenciamento de sessões, autenticação e tratamento de requisições HTTP.

**Flask-APScheduler**  
Extensão que integra o APScheduler ao Flask, permitindo a execução automática de tarefas em background em intervalos definidos, sem depender de requisições do usuário.

**PyMongo**  
Driver oficial do MongoDB para Python, responsável pela conexão com o banco de dados e pela realização de operações CRUD em documentos BSON.

**python-dotenv**  
Biblioteca utilizada para carregar variáveis de ambiente a partir de arquivos `.env`, garantindo maior segurança no uso de credenciais e configurações sensíveis.

**bson**  
Biblioteca usada para manipulação de `ObjectId`, o identificador padrão dos documentos armazenados no MongoDB.

**datetime**  
Biblioteca padrão do Python utilizada para manipulação de datas e horários, comparação de períodos, uso de timezone (UTC) e cálculo de intervalos de tempo.

**os**  
Biblioteca padrão do Python utilizada para acesso a variáveis de ambiente e integração com o sistema operacional.
