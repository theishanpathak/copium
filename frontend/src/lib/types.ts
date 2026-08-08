export type Card = {
  id: string;
  company: string;
  role: string;
  roast: string;
  quote: string | null;
  receivedAt: string | null;
  seq: number;
  viewed: boolean;
  published: boolean;
};