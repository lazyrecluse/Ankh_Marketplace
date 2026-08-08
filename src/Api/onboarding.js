import { post } from './client';

export const submitBuyerOnboarding = (profile) =>
    post('/api/onboarding/buyer', profile, { auth: true });

export const submitSupplierOnboarding = (profile) =>
    post('/api/onboarding/supplier', profile, { auth: true });
