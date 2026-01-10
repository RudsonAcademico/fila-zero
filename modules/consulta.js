import mongoose from 'mongoose';

const ConsultaSchema = new mongoose.Schema({
    cliente: {
        nome: { type: String, required: true },
        telefone: { type: String, required: true }
    },

    tipo: {
        type: String,
        enum: ['dentista', 'pediatra', 'clinico_geral', 'outros'],
        required: true
    },

    dataConsulta: {
        type: Date,
        required: true
    },

    status: {
        type: String,
        enum: ['nova', 'em_analise', 'confirmada', 'cancelada'],
        default: 'nova'
    },

    atendente: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User'
    }
}, { timestamps: true });

export default mongoose.model('Consulta', ConsultaSchema);