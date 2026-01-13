import { useState } from "react";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "./ui/button";
import CustomEAGenerator from "@/pages/CustomEAGenerator";
import { LogOut, LogIn } from "lucide-react";
import { useNavigate } from "react-router-dom";

export const StrategyBuilder = () => {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    await signOut();
    navigate('/auth');
  };

  return (
    <div className="min-h-screen bg-background grid-pattern">
      <div className="container mx-auto py-8 px-4">
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <div className="text-center flex-1">
              <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                Quantum Strategy Builder
              </h1>
              <p className="text-muted-foreground">
                Build institutional-grade mechanical trading strategies
              </p>
            </div>
            <div className="flex gap-2">
              {user ? (
                <Button variant="outline" onClick={handleSignOut}>
                  <LogOut className="w-4 h-4 mr-2" />
                  Sign Out
                </Button>
              ) : (
                <Button variant="outline" onClick={() => navigate('/auth')}>
                  <LogIn className="w-4 h-4 mr-2" />
                  Sign In
                </Button>
              )}
            </div>
          </div>
        </div>

        <Card className="card-elevated bg-card/50 backdrop-blur-sm border-border p-6">
          <CustomEAGenerator isEmbedded={true} />
        </Card>
      </div>
    </div>
  );
};
