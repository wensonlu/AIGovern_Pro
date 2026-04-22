#!/usr/bin/env node

import { readdir, readFile } from 'fs/promises';
import { join } from 'path';
import { writeFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PHASE_MAP = {
  'requirement-analysis': 'define',
  'system-design': 'plan',
  'frontend-implementation': 'build',
  'backend-api-development': 'build',
  'rag-pipeline': 'build',
  'integration-testing': 'verify',
  'code-review': 'review',
  'deployment': 'ship',
};

function extractTriggers(content) {
  const triggers = [];
  const patterns = [
    /## Triggers\n([\s\S]*?)(?=\n##|$)/,
  ];

  for (const pattern of patterns) {
    const match = content.match(pattern);
    if (match) {
      const lines = match[1].split('\n');
      lines.forEach(line => {
        const item = line.replace(/^-\s+/, '').trim();
        if (item && item.length > 0) {
          triggers.push(item.toLowerCase());
        }
      });
    }
  }

  return [...new Set(triggers)];
}

function extractKeywords(content) {
  const match = content.match(/## Keywords\n\n([\s\S]*?)(?=\n##|$)/);
  if (match) {
    return match[1]
      .split(',')
      .map(k => k.trim().toLowerCase())
      .filter(k => k.length > 0);
  }
  return [];
}

function inferPhase(skillId, content) {
  if (PHASE_MAP[skillId]) return PHASE_MAP[skillId];

  const lower = content.toLowerCase();
  if (lower.includes('define')) return 'define';
  if (lower.includes('plan')) return 'plan';
  if (lower.includes('build')) return 'build';
  if (lower.includes('verify')) return 'verify';
  if (lower.includes('review')) return 'review';
  if (lower.includes('ship')) return 'ship';
  return 'build';
}

async function parseSkillFile(filePath) {
  try {
    const content = await readFile(filePath, 'utf-8');

    // Extract description
    const descMatch = content.match(/description:\s*(.+)/);
    const description = descMatch ? descMatch[1].trim() : '';

    // Extract name
    const nameMatch = content.match(/^#\s+(.+)$/m);
    const name = nameMatch ? nameMatch[1].trim() : '';

    // Calculate skillId
    const parts = filePath.split('/');
    const skillId = parts[parts.length - 2] || name.toLowerCase().replace(/\s+/g, '-');

    // Extract phase
    const phaseMatch = content.match(/^phase:\s*(.+)$/m);
    let phase = phaseMatch ? phaseMatch[1].trim().toLowerCase() : inferPhase(skillId, content);

    // Extract triggers
    const triggers = extractTriggers(content);

    // Extract keywords
    const keywords = extractKeywords(content);

    return {
      id: skillId,
      name,
      description,
      phase,
      triggers: triggers.length > 0 ? triggers : keywords,
      triggersStyle: 'manual',
      dependsOn: [],
      relatedSkills: [],
      keywords: keywords.length > 0 ? keywords : triggers,
      filePath,
    };
  } catch (error) {
    console.error(`Failed to parse ${filePath}:`, error.message);
    return null;
  }
}

async function generateSkillsGraph() {
  const skillsPath = join(__dirname, '../.claude/skills');
  const outputDir = join(__dirname, '../public');
  const outputPath = join(outputDir, 'skills-graph.json');

  try {
    console.log('📖 Parsing skills from:', skillsPath);
    const nodes = [];
    const edges = [];

    const entries = await readdir(skillsPath, { withFileTypes: true });

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;

      const skillDir = join(skillsPath, entry.name);
      const skillFile = join(skillDir, 'SKILL.md');

      const node = await parseSkillFile(skillFile);
      if (node) {
        nodes.push(node);
      }
    }

    // Build phase-based edges
    const phaseOrder = ['define', 'plan', 'build', 'verify', 'review', 'ship'];

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const iPhaseIdx = phaseOrder.indexOf(nodes[i].phase);
        const jPhaseIdx = phaseOrder.indexOf(nodes[j].phase);
        if (jPhaseIdx > iPhaseIdx) {
          edges.push({
            from: nodes[i].id,
            to: nodes[j].id,
            type: 'depends',
          });
        }
      }
    }

    // Ensure output directory exists
    mkdirSync(outputDir, { recursive: true });

    const graph = { nodes, edges };
    writeFileSync(outputPath, JSON.stringify(graph, null, 2));

    console.log(`✅ Skills graph generated: ${outputPath}`);
    console.log(`📊 Found ${graph.nodes.length} skills, ${graph.edges.length} edges`);

    // Print summary by phase
    console.log('\n📈 Skills by phase:');
    phaseOrder.forEach(phase => {
      const count = graph.nodes.filter(n => n.phase === phase).length;
      if (count > 0) {
        console.log(`   ${phase.padEnd(8)}: ${count} skill(s)`);
      }
    });

  } catch (error) {
    console.error('❌ Error generating skills graph:', error);
    process.exit(1);
  }
}

generateSkillsGraph();
