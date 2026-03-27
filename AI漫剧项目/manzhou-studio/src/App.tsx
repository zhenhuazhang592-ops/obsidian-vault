import { useStore } from '@/store';
import { Header, STEPS, STEP_OUTPUT_KEYS } from '@/components/Header';
import {
  Step00,
  Step01,
  Step02,
  Step03,
  Step04,
  Step05,
  Step06,
  AssetLibrary,
} from '@/components/steps';

function StepContent({ step }: { step: number }) {
  switch (step) {
    case 0: return <Step00 />;
    case 1: return <Step01 />;
    case 2: return <Step02 />;
    case 3: return <Step03 />;
    case 4:
      return (
        <>
          <Step04 />
          <AssetLibrary type="character" title="🎭 角色资产库" />
          <AssetLibrary type="scene" title="🖼️ 场景资产库" />
        </>
      );
    case 5: return <Step05 />;
    case 6: return <Step06 />;
    default: return null;
  }
}

export default function App() {
  const { currentStep, setCurrentStep, outputs } = useStore();

  function isStepDone(step: number) {
    const key = STEP_OUTPUT_KEYS[step]!;
    return !!outputs[key];
  }

  return (
    <div>
      <Header />
      <div className="app-body">
        {/* Sidebar */}
        <nav className="sidebar">
          <div className="sidebar-label">WORKFLOW</div>
          {STEPS.map((s) => {
            const done = isStepDone(s.id);
            const active = currentStep === s.id;
            return (
              <button
                key={s.id}
                type="button"
                className={`sidebar-btn ${active ? 'sidebar-btn--active' : ''} ${done && !active ? 'sidebar-btn--done' : ''}`}
                onClick={() => setCurrentStep(s.id)}
              >
                <span className="sidebar-btn-icon">
                  {done && !active ? '✓' : s.icon}
                </span>
                <span>{s.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Main Workspace */}
        <main className="workspace">
          <div className="workspace-inner">
            <StepContent step={currentStep} />
          </div>
        </main>
      </div>
    </div>
  );
}
