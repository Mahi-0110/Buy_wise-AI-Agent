"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Search, Loader2, CheckCircle2, ShieldAlert, XCircle, ShoppingBag, ShieldCheck, ChevronRight, Activity, Zap, RefreshCw } from 'lucide-react';
import { planShopping, preparePurchase, authorizePurchase } from '@/lib/api';

type Product = {
  canonical_id: string;
  brand: string;
  model: string;
  best_price: number;
  best_store: string;
  specs: Record<string, string | number>;
  rating: number;
  delivery_days: number;
  thumbnail?: string | null;
  score?: number;
  product_url?: string;
  title?: string;
};

export default function Dashboard() {
  const [goal, setGoal] = useState("");
  const [loading, setLoading] = useState(false);
  const [timeline, setTimeline] = useState<string[]>([]);
  const [session, setSession] = useState<{ id: string, winner: Product | null, rationale: string, candidates: Product[] } | null>(null);
  
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [receipt, setReceipt] = useState<{ order_id: string; timestamp: string; amount_paid: number } | null>(null);
  const [spikeSimulated, setSpikeSimulated] = useState(false);
  const [haltedMessage, setHaltedMessage] = useState<string | null>(null);
  const [currentPrice, setCurrentPrice] = useState<number>(0);

  const timelineEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    timelineEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [timeline]);

  const handleDemoClick = (text: string) => {
    setGoal(text);
  };

  const startPipeline = async () => {
    if (!goal) return;
    setLoading(true);
    setTimeline(["[INIT] Connecting to BUYWISE Agent Engine..."]);
    setSession(null);
    setReceipt(null);
    setHaltedMessage(null);
    
    try {
      const progressInterval = setInterval(() => {
        setTimeline(prev => {
          if (prev.length < 5) return [...prev, "Processing..."];
          return prev;
        });
      }, 800);
      
      const data = await planShopping(goal);
      clearInterval(progressInterval);
      
      setTimeline(data.timeline);
      setSession({
        id: data.session_id,
        winner: data.winner,
        rationale: data.tradeoff_rationale,
        candidates: data.top_candidates
      });
    } catch {
      setTimeline(prev => [...prev, "[ERROR] Pipeline failed. Check backend connection."]);
    } finally {
      setLoading(false);
    }
  };

  const handlePrepare = async () => {
    if (!session?.winner) return;
    setAuthLoading(true);
    try {
      const data = await preparePurchase(session.id, spikeSimulated);
      if (data.status === "halted") {
        setHaltedMessage(data.message);
        setCurrentPrice(data.product.best_price);
      } else {
        setCurrentPrice(data.product.best_price);
      }
      setShowAuthModal(true);
    } catch (err) {
      console.error(err);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleAuthorize = async () => {
    if (!session) return;
    setAuthLoading(true);
    try {
      const data = await authorizePurchase(session.id, true, currentPrice);
      if (data.status === "success") {
        setReceipt(data.receipt);
        setShowAuthModal(false);
      }
    } catch (err) {
      console.error(err);
      alert("Authorization failed. Price may have mismatched.");
    } finally {
      setAuthLoading(false);
    }
  };

  return (
    <main className="max-w-6xl mx-auto p-6 space-y-8 pb-20">
      
      <header className="flex items-center justify-between py-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="bg-blue-500/20 p-2 rounded-lg text-blue-400">
            <Activity size={28} />
          </div>
          <h1 className="text-2xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
            BUYWISE <span className="text-sm font-medium text-slate-400">Prototype Edition</span>
          </h1>
        </div>
        
        <div className="flex items-center gap-3 bg-slate-800/50 px-4 py-2 rounded-full border border-slate-700">
          <span className="text-sm text-slate-300">Simulate Price Spike on Recheck</span>
          <button 
            onClick={() => setSpikeSimulated(!spikeSimulated)}
            className={`w-12 h-6 rounded-full transition-colors relative flex items-center ${spikeSimulated ? 'bg-red-500' : 'bg-slate-600'}`}
          >
            <div className={`w-4 h-4 bg-white rounded-full mx-1 transition-transform ${spikeSimulated ? 'translate-x-6' : 'translate-x-0'}`} />
          </button>
        </div>
      </header>

      <section className="glass-panel p-6 space-y-4">
        <h2 className="text-lg font-medium text-slate-200">What are you looking for?</h2>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
            <input 
              type="text" 
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g., Wireless headphones under ₹3,000 with ≥20h battery, preferably Sony or JBL"
              className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-100 placeholder:text-slate-500"
              onKeyDown={(e) => e.key === 'Enter' && startPipeline()}
            />
          </div>
          <button 
            onClick={startPipeline}
            disabled={loading || !goal}
            className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-4 rounded-xl font-semibold transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? <Loader2 className="animate-spin" /> : <Zap />}
            Run Agent
          </button>
        </div>
        
        <div className="flex gap-2 flex-wrap">
          <button onClick={() => handleDemoClick("Wireless headphones under ₹3000 with ≥20h battery, preferably Sony or JBL")} className="text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 px-3 py-1.5 rounded-full text-slate-300 transition-colors">
            Demo: Sony vs JBL Headphones
          </button>
          <button onClick={() => handleDemoClick("Headphones with noise cancellation under ₹5000")} className="text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 px-3 py-1.5 rounded-full text-slate-300 transition-colors">
            Demo: Noise Cancellation Focus
          </button>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <section className="glass-panel p-6 lg:col-span-1 h-[500px] flex flex-col">
          <div className="flex items-center gap-2 mb-4 border-b border-white/10 pb-4">
            <Activity className="text-emerald-400" size={20} />
            <h2 className="text-lg font-medium text-slate-200">Agent Timeline</h2>
          </div>
          <div className="flex-1 overflow-y-auto space-y-3 pr-2 font-mono text-sm">
            {timeline.length === 0 && <p className="text-slate-500 italic">Waiting for command...</p>}
            {timeline.map((event, i) => (
              <div key={i} className="timeline-item p-3 bg-slate-900/50 rounded-lg border border-slate-800/50 text-slate-300 flex items-start gap-2">
                <ChevronRight size={16} className="text-blue-500 shrink-0 mt-0.5" />
                <span className={event.includes("ERROR") || event.includes("FAILED") ? "text-red-400" : ""}>{event}</span>
              </div>
            ))}
            <div ref={timelineEndRef} />
          </div>
        </section>

        <section className="lg:col-span-2 flex flex-col gap-6">
          {session?.winner ? (
            (() => {
              const product = session.winner;
              return (
            <div className="space-y-6">
              <div className="glass-panel p-6 border-emerald-500/30 relative overflow-hidden">
                <div className="absolute top-0 right-0 bg-emerald-500/20 text-emerald-400 text-xs font-bold px-4 py-1 rounded-bl-lg flex items-center gap-1">
                  <ShieldCheck size={14} /> BUYWISE Verified Match
                </div>
                
                <h2 className="text-xl font-bold text-white mb-2">Recommendation Ready</h2>
                
                <div className="bg-slate-900/50 p-5 rounded-xl border border-slate-700 mt-4 flex items-center gap-4">
                  {/* Product Image - using standard HTML img tag */}
                  <div className="w-32 h-32 flex-shrink-0">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={product.thumbnail || undefined} alt={product.title || product.model} className="w-full h-48 object-cover rounded-xl bg-slate-800" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm text-slate-400">{product.brand}</div>
                    <div className="text-2xl font-bold text-slate-100">{product.model}</div>
                    <div className="mt-2 flex flex-wrap gap-3 text-sm">
                      <span className="bg-slate-800 px-2 py-1 rounded text-slate-300">₹{product.best_price}</span>
                      <span className="bg-slate-800 px-2 py-1 rounded text-slate-300">Store: {product.best_store}</span>
                      <span className="bg-slate-800 px-2 py-1 rounded text-slate-300">{product.specs.battery_hours || 'N/A'}h Battery</span>
                    </div>
                  </div>
                  <div className="flex flex-col items-center justify-center bg-blue-500/10 border border-blue-500/20 w-24 h-24 rounded-full flex-shrink-0">
                    <span className="text-3xl font-bold text-blue-400">{product.score}</span>
                    <span className="text-xs text-blue-400/80 uppercase tracking-wider">Score</span>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-slate-800/30 rounded-lg border border-slate-700/50">
                  <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">AI Trade-off Rationale</h3>
                  <p className="text-slate-200 leading-relaxed text-lg italic">&quot;{session.rationale}&quot;</p>
                </div>

                <div className="mt-6 flex justify-end gap-3">
                  <button 
                    onClick={handlePrepare}
                    disabled={authLoading}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center gap-2"
                  >
                    {authLoading ? <Loader2 className="animate-spin" /> : <ShoppingBag />}
                    Approve & Prepare Purchase
                  </button>
                </div>
              </div>
              
              {session.candidates && session.candidates.length > 1 && (
                <div className="glass-panel p-6">
                  <h3 className="text-lg font-medium text-slate-200 mb-4">Alternative Options</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {session.candidates
                      .filter(c => c.canonical_id !== product.canonical_id)
                      .slice(0, 4)
                      .map((alt, idx) => (
                      <div key={idx} className="bg-slate-900/50 p-4 rounded-xl border border-slate-700/50 flex gap-4">
                        <div className="w-20 h-20 flex-shrink-0">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img src={alt.thumbnail || undefined} alt={alt.title || alt.model} className="w-full h-full object-cover rounded-lg bg-slate-800" />
                        </div>
                        <div className="flex-1 flex flex-col justify-between">
                          <div>
                            <div className="text-xs text-slate-400">{alt.brand}</div>
                            <div className="text-sm font-bold text-slate-200 line-clamp-2">{alt.model}</div>
                            <div className="text-emerald-400 font-medium text-sm mt-1">₹{alt.best_price}</div>
                          </div>
                          {alt.product_url && (
                            <a 
                              href={alt.product_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-blue-400 hover:text-blue-300 inline-flex items-center gap-1 mt-2 w-fit"
                            >
                              Store Link <ChevronRight size={12} />
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
              );
            })()
          ) : (
            <div className="glass-panel p-6 flex flex-col items-center justify-center text-center h-[500px] text-slate-500">
               {loading ? (
                 <>
                  <RefreshCw className="animate-spin text-blue-500 mb-4" size={48} />
                  <p>Agent is evaluating options...</p>
                 </>
               ) : (
                 <p>Run the agent to see recommendations.</p>
               )}
            </div>
          )}
        </section>

      </div>

      {showAuthModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200">
            
            <div className={`p-6 ${haltedMessage ? 'bg-red-500/10' : 'bg-blue-500/10'} border-b border-slate-800`}>
              <div className="flex items-center gap-3">
                {haltedMessage ? <ShieldAlert className="text-red-500" size={28} /> : <ShieldCheck className="text-blue-500" size={28} />}
                <h2 className="text-xl font-bold text-white">Human Authorization Gate</h2>
              </div>
              <p className="text-slate-400 text-sm mt-2">AI cannot spend money. Explicit approval required.</p>
            </div>

            <div className="p-6 space-y-4">
              {haltedMessage && (
                <div className="bg-red-500/20 border border-red-500/50 p-4 rounded-lg text-red-200 text-sm flex items-start gap-2">
                  <XCircle className="shrink-0 mt-0.5" size={16} />
                  {haltedMessage}
                </div>
              )}

              <div className="bg-slate-800 rounded-lg p-4 space-y-3 text-sm">
                <div className="flex justify-between border-b border-slate-700 pb-2">
                  <span className="text-slate-400">Store</span>
                  <span className="font-medium text-white">{session?.winner?.best_store}</span>
                </div>
                <div className="flex justify-between border-b border-slate-700 pb-2">
                  <span className="text-slate-400">Item</span>
                  <span className="font-medium text-white truncate max-w-[200px]">{session?.winner?.model}</span>
                </div>
                <div className="flex justify-between border-b border-slate-700 pb-2">
                  <span className="text-slate-400">Est. Delivery</span>
                  <span className="font-medium text-white">{session?.winner?.delivery_days} days</span>
                </div>
                <div className="flex justify-between pt-2">
                  <span className="text-slate-300 font-medium">Total Price</span>
                  <span className={`font-bold text-lg ${haltedMessage ? 'text-red-400' : 'text-emerald-400'}`}>₹{currentPrice}</span>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button 
                  onClick={() => setShowAuthModal(false)}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-white py-3 rounded-lg font-medium transition-colors"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleAuthorize}
                  disabled={authLoading}
                  className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-colors ${haltedMessage ? 'bg-orange-600 hover:bg-orange-500 text-white' : 'bg-emerald-600 hover:bg-emerald-500 text-white'}`}
                >
                  {authLoading ? <Loader2 className="animate-spin" size={18} /> : null}
                  {haltedMessage ? 'Authorize Anyway' : 'Authorize Transaction'}
                </button>
              </div>
            </div>

          </div>
        </div>
      )}

      {receipt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="bg-emerald-950/90 border border-emerald-500/50 rounded-2xl w-full max-w-md p-8 shadow-2xl text-center space-y-4 animate-in fade-in slide-in-from-bottom-4">
            <div className="mx-auto w-16 h-16 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mb-6">
              <CheckCircle2 size={32} />
            </div>
            <h2 className="text-2xl font-bold text-emerald-500">Purchase Verified!</h2>
            <p className="text-slate-300 text-sm">Your order has been successfully placed.</p>
            
            <div className="bg-slate-900/50 rounded-lg p-4 text-left text-sm text-slate-400 space-y-2 mt-6">
              <div className="flex justify-between"><span>Order ID:</span> <span className="font-mono text-emerald-300">{receipt.order_id}</span></div>
              <div className="flex justify-between"><span>Timestamp:</span> <span>{new Date(receipt.timestamp).toLocaleString()}</span></div>
              <div className="flex justify-between"><span>Amount Paid:</span> <span className="text-white">₹{receipt.amount_paid}</span></div>
            </div>

            <button 
              onClick={() => { setReceipt(null); setSession(null); setTimeline([]); setGoal(""); }}
              className="mt-6 bg-emerald-600 hover:bg-emerald-500 text-white w-full py-3 rounded-lg font-medium transition-colors"
            >
              Start New Session
            </button>
          </div>
        </div>
      )}

    </main>
  );
}
