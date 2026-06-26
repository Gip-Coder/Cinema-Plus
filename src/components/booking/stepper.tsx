"use client";

import { Check } from "lucide-react";

interface StepperProps {
  currentStep: number; // 1 to 5
}

const STEPS = [
  { number: 1, label: "Choose Movie" },
  { number: 2, label: "Select Seats" },
  { number: 3, label: "Review Booking" },
  { number: 4, label: "Simulate Payment" },
  { number: 5, label: "Confirmation" },
];

export default function BookingStepper({ currentStep }: StepperProps) {
  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between relative">
        {/* Background connector line */}
        <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-0.5 bg-white/[0.06] -z-10" />
        
        {/* Active connector line */}
        <div 
          className="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 bg-red-500 transition-all duration-500 ease-out -z-10" 
          style={{ width: `${((currentStep - 1) / (STEPS.length - 1)) * 100}%` }}
        />

        {STEPS.map((step) => {
          const isCompleted = currentStep > step.number;
          const isActive = currentStep === step.number;
          
          return (
            <div key={step.number} className="flex flex-col items-center gap-2">
              <div 
                className={`
                  w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold text-xs transition-all duration-300
                  ${isCompleted 
                    ? "bg-red-600 border-red-500 text-white shadow-lg shadow-red-600/20" 
                    : isActive 
                    ? "bg-[hsl(222,84%,4.9%)] border-red-500 text-red-500 scale-110 shadow-md shadow-red-500/10" 
                    : "bg-[hsl(222,84%,2.5%)] border-white/10 text-zinc-500"
                  }
                `}
              >
                {isCompleted ? (
                  <Check className="h-4 w-4 stroke-[3]" />
                ) : (
                  <span>{step.number}</span>
                )}
              </div>
              <span 
                className={`
                  text-[10px] sm:text-xs font-semibold tracking-wide transition-colors duration-300
                  ${isActive ? "text-red-400" : isCompleted ? "text-zinc-300" : "text-zinc-500"}
                `}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
