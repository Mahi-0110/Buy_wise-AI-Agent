import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const planShopping = async (goal: string) => {
    const res = await axios.post(`${API_BASE}/shopping/plan`, { goal });
    return res.data;
};

export const preparePurchase = async (sessionId: string, triggerPriceSpike: boolean = false) => {
    const res = await axios.post(`${API_BASE}/purchase/prepare`, {
        session_id: sessionId,
        trigger_price_spike: triggerPriceSpike
    });
    return res.data;
};

export const authorizePurchase = async (sessionId: string, authorized: boolean, expectedPrice: number) => {
    const res = await axios.post(`${API_BASE}/purchase/authorize`, {
        session_id: sessionId,
        authorized,
        expected_price: expectedPrice
    });
    return res.data;
};
