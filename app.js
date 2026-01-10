import express from 'express';
import mongoose from 'mongoose';
import 'dotenv/config';

const app = express();

app.use(express.json());

/* =========================
    Conexão com MongoDB
========================= */
mongoose.connect(process.env.MONGO_URI)
    .then(() => console.log('✅ MongoDB conectado'))
    .catch(err => console.error('❌ Erro MongoDB:', err));

/* =========================
        Rotas
========================= */

// Tela de login
app.get('/login', (req, res) => {
    res.json({
        tela: 'login',
        mensagem: 'Tela de login'
    });
});

// Tela de dashboard (futura rota protegida)
app.get('/dashboard', (req, res) => {
    res.json({
        tela: 'dashboard',
        mensagem: 'Painel administrativo'
    });
});

/* =========================
    Inicialização do servidor
========================= */
const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
    console.log(`🚀 Servidor rodando na porta ${PORT}`);
});
