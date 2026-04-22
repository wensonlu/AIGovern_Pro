import React from 'react';
import { Progress, Space } from 'antd';
import type { SkillGraph, ProjectState, SkillPhase } from '../types/skills';
import styles from './ProjectTrackerPanel.module.css';

interface ProjectTrackerPanelProps {
  project: ProjectState;
  graph: SkillGraph;
  onSkillComplete?: (skillId: string) => void;
}

const PHASE_ORDER: SkillPhase[] = ['define', 'plan', 'build', 'verify', 'review', 'ship'];

const ProjectTrackerPanel: React.FC<ProjectTrackerPanelProps> = ({
  project,
  graph,
  onSkillComplete,
}) => {
  const currentIndex = PHASE_ORDER.indexOf(project.currentPhase);

  return (
    <div className={styles.container}>
      <h2 style={{ marginBottom: '24px' }}>{project.name}</h2>
      <div className={styles.phaseProgress}>
        {PHASE_ORDER.map((phase, idx) => {
          const isActive = idx === currentIndex;
          const isPast = idx < currentIndex;
          const skills = graph.nodes.filter((n) => n.phase === phase);
          const completedCount = skills.filter((s) => project.completedSkills.includes(s.id))
            .length;
          const progress = skills.length > 0 ? (completedCount / skills.length) * 100 : 0;

          return (
            <div
              key={phase}
              className={`${styles.phaseColumn} ${isActive ? styles.active : ''} ${
                isPast ? styles.past : ''
              }`}
            >
              <div className={styles.phaseHeader}>
                <div>{phase.toUpperCase()}</div>
                <Progress
                  type="circle"
                  percent={Math.round(progress)}
                  width={50}
                  strokeColor={progress === 100 ? '#52c41a' : '#1890ff'}
                />
              </div>
              <div className={styles.phaseSkills}>
                {skills.map((skill) => (
                  <div
                    key={skill.id}
                    className={`${styles.skillItem} ${
                      project.completedSkills.includes(skill.id) ? styles.done : ''
                    }`}
                    onClick={() => onSkillComplete?.(skill.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    {skill.name}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ProjectTrackerPanel;
