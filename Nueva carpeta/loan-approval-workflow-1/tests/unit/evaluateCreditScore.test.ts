import { evaluateCreditScore } from '../../src/functions/evaluateCreditScore/index';

describe('evaluateCreditScore', () => {
    it('should return true for a credit score above 700', () => {
        const result = evaluateCreditScore(750);
        expect(result).toBe(true);
    });

    it('should return false for a credit score below 600', () => {
        const result = evaluateCreditScore(580);
        expect(result).toBe(false);
    });

    it('should return false for a credit score between 600 and 700', () => {
        const result = evaluateCreditScore(650);
        expect(result).toBe(false);
    });

    it('should handle invalid input gracefully', () => {
        const result = evaluateCreditScore(null);
        expect(result).toBe(false);
    });
});