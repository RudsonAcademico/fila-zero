import mongoose from 'mongoose';

const UserSchema = new mongoose.Schema({
    nome: { type: String, required: true },
    email: { type: String, unique: true, required: true },
    senha: { type: String, required: true },
    role: {
        type: String,
        enum: ['admin', 'funcionario'],
        default: 'funcionario'
    }
}, { timestamps: true });

export default mongoose.model('User', UserSchema);