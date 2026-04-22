export type SkillPhase = 'define' | 'plan' | 'build' | 'verify' | 'review' | 'ship';

export interface SkillNode {
  id: string;
  name: string;
  description: string;
  phase: SkillPhase;
  triggers: string[];
  triggersStyle: 'auto' | 'manual';
  dependsOn: string[];
  relatedSkills: string[];
  keywords: string[];
  filePath: string;
}

export interface ProjectState {
  id: string;
  name: string;
  currentPhase: SkillPhase;
  completedSkills: string[];
  blockedBy: string[];
}

export interface SkillEdge {
  from: string;
  to: string;
  type: 'depends' | 'relates';
}

export interface SkillGraph {
  nodes: SkillNode[];
  edges: SkillEdge[];
}

export interface SkillRecommendation {
  skill: SkillNode;
  reason: string;
}
