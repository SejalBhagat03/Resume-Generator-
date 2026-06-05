import re

class KnowledgeGraphRenderer:
    @staticmethod
    def render_graph_html(resume_data: dict) -> str:
        """
        Generates an HTML string containing an interactive SVG Knowledge Graph mapping
        Skills directly to Projects and Experience where they are demonstrated.
        """
        # 1. Parse skills
        skills_section = resume_data.get("technical_skills", {})
        skills = []
        for cat, val in skills_section.items():
            if val:
                for s in re.split(r"[,;]", val):
                    s_clean = s.strip()
                    if s_clean:
                        skills.append(s_clean)
        skills = sorted(list(set(skills)))

        # 2. Parse targets (Projects & Experience)
        projects = resume_data.get("projects", [])
        experience = resume_data.get("experience", [])
        
        targets = []
        for p in projects:
            targets.append({
                "id": f"proj_{len(targets)}",
                "name": p.get("title", "Project"),
                "type": "project",
                "text": f"{p.get('title', '')} {p.get('tools', '')} " + " ".join(p.get("bullets", []))
            })
        for e in experience:
            targets.append({
                "id": f"exp_{len(targets)}",
                "name": f"{e.get('role', 'Role')} ({e.get('company', 'Company')})",
                "type": "experience",
                "text": f"{e.get('role', '')} {e.get('company', '')} {e.get('technologies', '')} " + " ".join(e.get("bullets", []))
            })

        # 3. Create connections
        links = []
        for skill_idx, skill in enumerate(skills):
            skill_lower = skill.lower()
            for target in targets:
                if re.search(rf"\b{re.escape(skill_lower)}\b", target["text"].lower()):
                    links.append({
                        "source": f"skill_{skill_idx}",
                        "target": target["id"]
                    })

        # If no skills or targets, provide a fallback visual message
        if not skills or not targets:
            return "<h3>Please add some skills and projects/experience to generate the Knowledge Graph.</h3>"

        # Generate SVG layout positions (Left column for Skills, Right column for Projects/Experience)
        height = max(400, max(len(skills), len(targets)) * 45)
        
        # Skill node positions
        skill_nodes = []
        skill_spacing = height / (len(skills) + 1)
        for i, skill in enumerate(skills):
            skill_nodes.append({
                "id": f"skill_{i}",
                "name": skill,
                "x": 120,
                "y": int((i + 1) * skill_spacing),
                "type": "skill"
            })

        # Target node positions
        target_nodes = []
        target_spacing = height / (len(targets) + 1)
        for i, target in enumerate(targets):
            target_nodes.append({
                "id": target["id"],
                "name": target["name"],
                "x": 680,
                "y": int((i + 1) * target_spacing),
                "type": target["type"]
            })

        all_nodes = skill_nodes + target_nodes

        # Generate JS node and link definitions
        nodes_js = json.dumps(all_nodes)
        links_js = json.dumps(links)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{
              font-family: 'Inter', sans-serif;
              background-color: #F8FAFC;
              margin: 0;
              padding: 10px;
              overflow: hidden;
            }}
            .node {{
              transition: all 0.25s ease;
              cursor: pointer;
            }}
            .node circle {{
              stroke-width: 2px;
            }}
            .node.skill circle {{
              fill: #6366F1;
              stroke: #4F46E5;
            }}
            .node.project circle {{
              fill: #10B981;
              stroke: #059669;
            }}
            .node.experience circle {{
              fill: #F59E0B;
              stroke: #D97706;
            }}
            .node text {{
              font-size: 11px;
              font-weight: 600;
              fill: #334155;
              pointer-events: none;
            }}
            .node.hover circle {{
              transform: scale(1.3);
              filter: drop-shadow(0 4px 6px rgba(0,0,0,0.15));
            }}
            .node.dim circle {{
              opacity: 0.25;
            }}
            .node.dim text {{
              opacity: 0.15;
            }}
            .link {{
              stroke: #CBD5E1;
              stroke-width: 1.5px;
              fill: none;
              transition: stroke 0.25s, stroke-width 0.25s;
            }}
            .link.highlight {{
              stroke: #6366F1;
              stroke-width: 3px;
              opacity: 1 !important;
            }}
            .link.dim {{
              opacity: 0.1;
            }}
          </style>
        </head>
        <body>
          <svg width="100%" height="{height}px" style="border: 1px solid #E2E8F0; border-radius: 12px; background: #fff;">
            <defs>
              <linearGradient id="link-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#6366F1" stop-opacity="0.6"/>
                <stop offset="100%" stop-color="#10B981" stop-opacity="0.6"/>
              </linearGradient>
            </defs>
            
            <g id="links-group"></g>
            <g id="nodes-group"></g>
          </svg>

          <script>
            const nodes = {nodes_js};
            const links = {links_js};

            const linksGroup = document.getElementById('links-group');
            const nodesGroup = document.getElementById('nodes-group');

            // 1. Render links
            links.forEach((l, idx) => {{
              const srcNode = nodes.find(n => n.id === l.source);
              const tgtNode = nodes.find(n => n.id === l.target);
              if (srcNode && tgtNode) {{
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                // Draw bezier curve connection
                const midX = (srcNode.x + tgtNode.x) / 2;
                const d = `M ${{srcNode.x}} ${{srcNode.y}} C ${{midX}} ${{srcNode.y}}, ${{midX}} ${{tgtNode.y}}, ${{tgtNode.x}} ${{tgtNode.y}}`;
                path.setAttribute('d', d);
                path.setAttribute('class', 'link');
                path.setAttribute('id', `link-${{idx}}`);
                path.dataset.source = l.source;
                path.dataset.target = l.target;
                linksGroup.appendChild(path);
              }}
            }});

            // 2. Render nodes
            nodes.forEach(n => {{
              const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
              g.setAttribute('class', `node ${{n.type}}`);
              g.setAttribute('id', n.id);
              // Set transform origin for scaling
              g.style.transformOrigin = `${{n.x}}px ${{n.y}}px`;

              const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
              circle.setAttribute('cx', n.x);
              circle.setAttribute('cy', n.y);
              circle.setAttribute('r', n.type === 'skill' ? 8 : 7);
              g.appendChild(circle);

              const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
              text.setAttribute('x', n.type === 'skill' ? n.x - 12 : n.x + 12);
              text.setAttribute('y', n.y + 4);
              text.setAttribute('text-anchor', n.type === 'skill' ? 'end' : 'start');
              text.textContent = n.name;
              g.appendChild(text);

              // Hover events
              g.addEventListener('mouseenter', () => highlightConnections(n.id));
              g.addEventListener('mouseleave', () => resetHighlight());

              nodesGroup.appendChild(g);
            }});

            function highlightConnections(nodeId) {{
              const activeLinks = [];
              
              // Find all connected links
              document.querySelectorAll('.link').forEach(link => {{
                if (link.dataset.source === nodeId || link.dataset.target === nodeId) {{
                  link.classList.add('highlight');
                  activeLinks.push(link);
                }} else {{
                  link.classList.add('dim');
                }}
              }});

              // Highlight connected nodes
              const connectedNodeIds = new Set([nodeId]);
              activeLinks.forEach(link => {{
                connectedNodeIds.add(link.dataset.source);
                connectedNodeIds.add(link.dataset.target);
              }});

              document.querySelectorAll('.node').forEach(node => {{
                if (connectedNodeIds.has(node.id)) {{
                  node.classList.add('hover');
                }} else {{
                  node.classList.add('dim');
                }}
              }});
            }}

            function resetHighlight() {{
              document.querySelectorAll('.link').forEach(link => {{
                link.classList.remove('highlight', 'dim');
              }});
              document.querySelectorAll('.node').forEach(node => {{
                node.classList.remove('hover', 'dim');
              }});
            }}
          </script>
        </body>
        </html>
        """
        return html
import json
