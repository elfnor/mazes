"""
The cell and grid structure used in maze_3d.py is similar
to the vertex and edge structure of a mesh.

This sverchok scripted node produces a maze for any mesh input


"""
import random
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
import bmesh
import mathutils

def edge_dict(n, edges):
    edge_dict = {k: [] for k in range(n)}
    for e in edges:
        edge_dict[e[0]].append(e[1])
        edge_dict[e[1]].append(e[0])
    return edge_dict

def recursive_back_tracker_maze(verts, edges):
    """
    verts: list of coordinates of vertices
    edges: list of pairs of vertex indices
    links: list of pairs of vertex connections that form a perfect maze
    """
    stack = [] 
    links = []
    ed = edge_dict(len(verts), edges)
    ld = {k: [] for k in range(len(verts))}
    stack.append(random.randint(0, len(verts) - 1))
    while len(stack) > 0: 
        current = stack[-1]
                        
        neighbors = [
            n 
            for n in ed[current]
                if len(ld[n]) == 0
        ]
                
        if len(neighbors)==0:
            stack.pop()
        else:
            neighbor = random.choice(neighbors)
            links.append([current, neighbor])	 
            stack.append(neighbor) 
            ld[current].append(neighbor)
            ld[neighbor].append(current)
 
    return links 

def do_braid(verts, edges, links, p=1.0):
    """
    Add links between dead ends (only one neighbour) and a neighbouring vertex
    p is the proportion (approx) of dead ends that are culled. Default p=1.0 removes 
    them all. 
    Linking dead ends produces loops in the maze.
    Prefer to link to another dead end if possible
    """       
    ed = edge_dict(len(verts), edges)
    ld = edge_dict(len(verts), links)
    ends = [i for i,v in enumerate(verts) if len(ld[i]) == 1]  
    random.shuffle(ends)
    braid_links = links[:]
    for v_id in ends:
        ngh_links = ld[v_id]
        if len(ngh_links) == 1 and (random.random() < p):
            #its still a dead end, ignore some if p < 1
            # find neighbours not linked to cell
            unlinked = [ngh for ngh in ed[v_id] if ngh not in ngh_links]
            
            #find unlinked neighbours that are also dead ends           
            best = [ngh for ngh in unlinked if len(ld[ngh]) == 1]
            if len(best) == 0:
                best = unlinked
            ngh = random.choice(best)    
            braid_links.append([v_id, ngh])
            ld[v_id].append(ngh)
            ld[ngh].append(v_id)
            
    return braid_links

def sv_main(verts=[],edges=[], faces=[], rseed=21, offset=20, braid = 0.0):
 
    in_sockets = [
        ['v', 'Vertices',  verts],
        ['s', 'Edges',  edges],
        ['s', 'Faces', faces],
        ['s', 'rseed', rseed],
        ['s', 'offset', offset],
        ['s', 'braid', braid]
    ]
    links = []
    verts_maze = []
    verts_path = []
    edges_path  = []
    faces_path = []
    verts_wall = []
    edges_wall  = []
    faces_wall = []
    
    random.seed(rseed) 
    
    if verts and edges:
        
        if faces:                   
            # don't use edges with a vertex on boundary for maze generation
            bm_maze = bmesh_from_pydata(verts[0], edges[0], faces[0])
            # make a list of boundary verts
            boundary_verts = [v for v in bm_maze.verts if v.is_boundary]
            #remove these verts
            bmesh.ops.delete(bm_maze, geom=boundary_verts, context=1)
            #convert back to sverchok lists and generate maze on these
            verts_maze, edges_maze, faces_maze = pydata_from_bmesh(bm_maze)  
            links = recursive_back_tracker_maze(verts_maze, edges_maze)  
            if braid > 0 and braid <= 1.0:
                links = do_braid(verts_maze, edges_maze, links, braid)
  
            bm_maze.free()                  
                                              
            #bevel the whole mesh
            bm = bmesh_from_pydata(verts[0], edges[0], faces[0])
            geom = list(bm.verts) + list(bm.edges) + list(bm.faces)                

            bevel_faces = bmesh.ops.bevel(bm, geom=geom, offset=offset,
                                    offset_type=3, segments=1,
                                    profile=0.5, vertex_only=0,
                                    material=-1)['faces']
            
            #match ids of bevelled face to links     
            #find center of each new face in bevel mesh
            face_centers = [f.calc_center_median() for f in bm.faces]        
            #make a kdtree from face centers of bevel faces
            kd = mathutils.kdtree.KDTree(len(face_centers))
            for i, c in enumerate(face_centers):
                kd.insert(c, i)
            kd.balance()   
                                
            #find center of each link in maze
            link_centers = []
            for e in links:
                x,y,z = zip(*[verts_maze[poi] for poi in e])
                x,y,z = sum(x)/len(x), sum(y)/len(y), sum(z)/len(z)
                link_centers.append((x,y,z)) 
                                   
            #find index of closest face center to the center of each link and each maze vertex     
            path_face_ids = [kd.find(v)[1] for v in verts_maze + link_centers]  

   
            #delete the walls form the path mesh
            bm_path = bm.copy()
            bm_path.faces.ensure_lookup_table()
            wall_faces = [
                bm_path.faces[id] 
                for id,fc in enumerate(face_centers) 
                    if id not in path_face_ids
            ]
            bmesh.ops.delete(bm_path, geom=wall_faces, context=5)
            
            verts_path, edges_path, faces_path = pydata_from_bmesh(bm_path)
            bm_path.free()
                      
            #delete the path from the wall mesh
            bm.faces.ensure_lookup_table()
            path_faces = list(set([bm.faces[id] for id in path_face_ids]))
            bmesh.ops.delete(bm, geom=path_faces, context=5)
            verts_wall, edges_wall, faces_wall = pydata_from_bmesh(bm)
            bm.free() 
            
        else:    
            # no faces just make links
            verts_maze = verts[0]
            links = recursive_back_tracker_maze(verts[0], edges[0])
       
    out_sockets = [
        ['v', 'Link Vertices', [verts_maze] ],
        ['s', 'Link Edges', [links]],
        ['v', 'Path Vertices', [verts_path]],
        ['s', 'Path Edges', [edges_path] ],
        ['s', 'Path Faces', [faces_path] ],
        ['v', 'Wall Vertices', [verts_wall]],
        ['s', 'Wall Edges', [edges_wall] ],
        ['s', 'Wall Faces', [faces_wall] ]
    ]
 
    return in_sockets, out_sockets
