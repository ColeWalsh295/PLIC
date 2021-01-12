import sys
import numpy as np
import pandas as pd
from itertools import combinations
import matplotlib
matplotlib.rcParams.update({'font.size': 28})
import matplotlib.pyplot as plt
plt.axis('off')
plt.style.use('seaborn-dark-palette')
import networkx as nx
from networkx.algorithms import bipartite
import community
import holoviews as hv
hv.extension('bokeh')
import chart_studio.plotly as py
import colorlover as cl

def Individiual_Question_Network(df, Question, Survey = 'PRE'):
    """Plot a network graph of PLIC items that are picked together on a single question.

    Keyword arguments:
    df -- pandas dataframe of PLIC student responses
    Question -- which question to plot items from
    Survey -- either PRE or POST
    """

    # these are 'other' options, which we remove
    Others = ['Q1b_19', 'Q1d_10', 'Q1e_12', 'Q2b_38', 'Q2d_11', 'Q2e_11', 'Q3b_10', 'Q3d_29', 'Q3e_8', 'Q4b_11']

    if(Survey == 'PRE'):
        appendix = 'x'
        df1 = df[df['Survey_x'] == 'C'] # get only closed-response surveys
    else:
        appendix = 'y'
        df1 = df[df['Survey_y'] == 'C']
    ID = 'V1_' + appendix

    # get items belonginging to specified question
    cols = [col for col in df1.columns if Question in col and col[:-2] not in Others and 'TEXT' not in col and 'l' not in col and appendix in col]
    df_Q = df1[[ID] + cols]
    df_Q.loc[:, cols] = df_Q.loc[:, cols].fillna(0).apply(pd.to_numeric, errors = 'coerce').fillna(1).replace(0, np.nan)
    cols = [col[:-2] for col in df_Q.columns]
    df_Q.columns = cols
    Node_Sizes = df_Q.fillna(0).sum(numeric_only = True).to_dict()
    df_Q_Bipartite = pd.melt(df_Q, id_vars = 'V1').dropna().reset_index(drop = True)[['V1', 'variable']].rename(columns = {'V1':'Student', 'variable':'item'})
    B = nx.from_pandas_edgelist(df_Q_Bipartite, 'Student', 'item')
    Used_items = list(set(df_Q_Bipartite['item']))
    G = bipartite.weighted_projected_graph(B, Used_items) # project student - items graph onto the items

    pos = nx.spring_layout(G, iterations = 50)
    nx.set_node_attributes(G, Node_Sizes, '# of Students')

    Node_Sizes_Array = []
    for node, data in G.nodes(data = True):
        Node_Sizes_Array.append(data['# of Students']) # we'll use number of students rather than a centrality measure as its more intuitive
    Node_Labels_dict = {node:node for node in G.nodes()}

    Edge_Colors_Array = []
    for node1, node2, data in G.edges(data = True):
        Edge_Colors_Array.append(data['weight'])

    nx.draw_networkx_nodes(G, pos = pos, node_size = Node_Sizes_Array)
    nx.draw_networkx_labels(G, pos = pos, labels = Node_Labels_dict)
    nx.draw_networkx_edges(G, pos = pos, edge_cmap = plt.cm.Greys, edge_color = Edge_Colors_Array, edge_vmin = min(Edge_Colors_Array),
                            edge_vmax = max(Edge_Colors_Array))
    plt.show()

def LANS(A, alpha = 0.05):
    """Locally adaptive network sparsification (LANS) algorithm to sparsify networks based on significance of edges for each node.

    Keyword arguments:
    A -- adjacency matrix
    alpha -- significance level of edges to keep; a lower number creates a sparser network
    """

    cutoff = (1 - alpha) * 100
    A[A == 0] = np.nan
    A = np.array(A)
    Cuts = np.nanpercentile(A, cutoff, axis = 1)
    C = np.array([A[i] * (A[i] > Cuts[i]) for i in range(A.shape[0])])
    C[np.isnan(C)] = 0

    for i in range(C.shape[0]):
        for j in range(C.shape[1]):
            if(C[i, j] != C[j, i]):
                C[i, j] = max(C[i, j], C[j, i])
                C[j, i] = max(C[i, j], C[j, i])

    return C

def FindCommunities(df, Survey = 'ALL', Matched = False, Projection = 'Item', resolution = 1, Community_Nodes = False, Iterate = False, Sparsify = False,
                        randomize = False, **kwargs):
    """Conduct module analysis using louvain method to find communities.

    Keyword arguments:
    df -- pandas dataframe of student responses
    Survey -- either PRE, POST, or ALL
    Matched -- binary; whether to only include matched responses in analysis
    Projection -- accepts either Item or Students; which level to perform community detection
    resolution -- a smaller resolution will create more smaller communities
    Community_Nodes -- whether to generate induced subgraph of network communities
    Iterate -- whether more than one instance of the algorithm will be run
    Sparsify -- whether to sparsify network using LANS algorithm
    randomize -- whether to randomize node evaluation and community evaluation, providing different partitions with each call
    kwargs -- optional keyword arguments to pass to LANS
    """

    # read in header information NEEDS UPDATING
    Infodf = pd.read_csv('C:/Users/Cole/Documents/GRA_Summer2018/Surveys/180202__PLIC__Working_version_3d_fix2.csv',
                            nrows = 1).T.rename(columns = {0:'Description'})
    Others = ['Q1b_19', 'Q1d_10', 'Q1e_12', 'Q2b_38', 'Q2d_11', 'Q2e_11', 'Q3b_10', 'Q3d_29', 'Q3e_8', 'Q4b_11'] # remove other columns

    if(Survey == 'PRE'):
        appendix = '_x'
        if Matched:
            df1 = df[(df['Survey_x'] == 'C') & (df['Survey_y'] == 'C')]
        else:
            df1 = df[df['Survey_x'] == 'C']
    elif(Survey == 'POST'):
        appendix = '_y'
        if Matched:
            df1 = df[(df['Survey_x'] == 'C') & (df['Survey_y'] == 'C')]
        else:
            df1 = df[df['Survey_y'] == 'C']
    else:
        appendix = ''
        if Matched:
            df1 = df[(df['Survey_x'] == 'C') & (df['Survey_y'] == 'C')]
        else:
            df1 = df[df['Survey_x'] == 'C']
            df2 = df[df['Survey_y'] == 'C']
    ID = 'V1' + appendix

    Questions = ['Q1b', 'Q1d', 'Q1e', 'Q2b', 'Q2d', 'Q2e', 'Q3b', 'Q3d', 'Q3e', 'Q4b']
    if(Survey != 'ALL'):
        cols = [col for col in df1.columns for Question in Questions if Question in col and col[:-2] not in Others and 'TEXT' not in col and 'l' not in col and appendix in col]
        df_total = df1[[ID] + cols]
        cols = [col[:-2] for col in df_total.columns]
        df_total.columns = cols
    else:
        cols1 = [col for col in df1.columns for Question in Questions if Question in col and col[:-2] not in Others and 'TEXT' not in col and 'l' not in col and '_x' in col]
        cols2 = [col for col in df2.columns for Question in Questions if Question in col and col[:-2] not in Others and 'TEXT' not in col and 'l' not in col and '_y' in col]

        df1 = df1[['V1_x'] + cols1]
        df2 = df2[['V1_y'] + cols2]

        cols = [col[:-2] for col in df1.columns]
        df1.columns = cols
        df2.columns = cols
        df_total = pd.concat([df1, df2], axis = 0)

    print(len(df_total))

    df_total.loc[:, cols[1:]] = df_total.loc[:, cols[1:]].fillna(0).apply(pd.to_numeric, errors = 'coerce').fillna(1).replace(0, np.nan)
    Node_Sizes = df_total.fillna(0).sum(numeric_only = True).to_dict()
    df_total_Bipartite = pd.melt(df_total, id_vars = 'V1').dropna().reset_index(drop = True)[['V1', 'variable']].rename(columns = {'V1':'Student',
                                    'variable':'item'})
    B = nx.from_pandas_edgelist(df_total_Bipartite, 'Student', 'item')

    if(Projection == 'Item'):
        Used_items = list(set(df_total_Bipartite['item']))
        G = bipartite.weighted_projected_graph(B, Used_items)
    elif(Projection == 'Students'):
        Students = list(set(df_total_Bipartite['Student']))
        G = bipartite.weighted_projected_graph(B, Students)

    Nodes_List = G.nodes()
    if Sparsify:
        A = nx.to_numpy_matrix(G)
        G1 = nx.convert_matrix.from_numpy_matrix(LANS(A, **kwargs))
        Mapping = {i:Node for i, Node in enumerate(Nodes_List)}
        G = nx.relabel_nodes(G1, Mapping)

    #louvain community detection
    Communities = community.best_partition(G, weight = 'weight', resolution = resolution, randomize = randomize)
    Communities_df = pd.DataFrame.from_dict(Communities, orient = 'index', columns = ['Community'])

    if(Projection == 'Item'):
        Communities2_df = pd.merge(left = Communities_df, right = Infodf, left_index = True, right_index = True) # add header info for descriptions
        Communities2_df['Description'] = Communities2_df['Description'].apply(lambda x: x.split('-')[-1])
        Communities2_df = Communities2_df.set_index('Community', append = True).sort_index(level = 1).reset_index(level = 1)

        nx.set_node_attributes(G, Node_Sizes, '# of Students')

    elif(Projection == 'Students'):
        Communities2_df = pd.merge(left = Communities_df, right = df1, left_index = True,
                                    right_on = ID).sort_values(by = ['Community']).rename(columns = {ID:'Students'}).set_index('Students')

        nx.set_node_attributes(G, Node_Sizes, '# of Items in common')

    if((not Iterate) and (Projection == 'Item')):
        print('Modularity: {}'.format(community.modularity(Communities, G, weight = 'weight')))

        nx.set_node_attributes(G, Communities, 'Community')

        G1 = hv.Graph.from_networkx(G, nx.spring_layout, iterations = 50).options(width = 500, height = 500, color_index = 'Community', cmap = 'tab10',
                                                                                    edge_color_index = 'weight', edge_cmap = 'Greys', show_frame = False,
                                                                                    xaxis = None, yaxis = None)

        D1 = community.generate_dendrogram(G, weight = 'weight', resolution = resolution) # dendrograms of communities were created step-by-step

        if Community_Nodes:
            I1 = community.induced_graph(Communities, G, weight = 'weight')

            I2 = nx.Graph()
            Node_Size_Array = []
            Edge_Width_Array = []
            for node1, node2, data in I1.edges(data = True):
                if(node1 == node2):
                    I2.add_node(node1)
                    Node_Size_Array.append(data['weight']/np.sqrt(8900))
            for node1, node2, data in I1.edges(data = True):
                if(node1 != node2):
                    I2.add_edge(node1, node2)
                    Edge_Width_Array.append(data['weight']/34000)
            Labels_Dict = {node:node for node in I2.nodes()}

            pos = nx.spring_layout(I2)

            nx.draw_networkx_nodes(I2, pos = pos, node_size = np.array(Node_Size_Array)/np.sqrt(min(Node_Size_Array)))
            nx.draw_networkx_labels(I2, pos = pos, labels = Labels_Dict)
            nx.draw_networkx_edges(I2, pos = pos, width = np.array(Edge_Width_Array)/min(Edge_Width_Array))
            plt.show()

            return Communities2_df, G1, D1, I2

        return Communities2_df, G1, D1

    else:
        return Communities2_df, G

def IterativeCommunityFinding(df, N_Iterations = 5, Community_Iters = 5, Cutoff = 0, Projection = 'Item', **kwargs):
    """Generate many partitions of the data to evaluate stability of solution.

    Keyword arguments:
    df -- pandas dataframe of student responses
    N_Iterations -- how many times to run the FindCommunities algorithm
    Community_Iters -- how many times to iteratively compare community belonging to generate aggregate communities
    Cutoff -- minimum fraction of iterations two items need to be partitioned into the same community to count in the aggregate communities
    Projection -- either Item or Students, which level to project network data
    kwargs -- optional keyword arguments to pass to FindCommunities
    """

    Community_Overlap = {}
    for n in range(N_Iterations):

        Community_df, G = FindCommunities(df, Projection = Projection, Iterate = True, randomize = True, **kwargs)
        for c in range(Community_df['Community'].max() + 1):
            Nodes_in_c = list(combinations(list(Community_df[Community_df['Community'] == c].index), 2))

            # add tuples of items in the same community in an iteration to the counter
            for t in Nodes_in_c:
                try:
                    Community_Overlap[t] += 1
                except:
                    try:
                        Community_Overlap[tuple([t[1], t[0]])] += 1 # check the reverse tuple if the forward one doesn't exist
                    except:
                        Community_Overlap[t] = 1 # otherwise this is the first time this tuple has appeared and we start the counter

    # turn that dictionary into a symmetric dataframe
    Overlap_df = pd.DataFrame()
    for t, value in Community_Overlap.items():
        Overlap_df.loc[t[0], t[1]] = value
        Overlap_df.loc[t[1], t[0]] = value

    Overlap_df = Overlap_df.loc[Community_df.index, Community_df.index]/N_Iterations
    Community_df = Community_df.reset_index().rename(columns = {'index':Projection})

    Coms = Community_df.groupby('Community')[Projection].apply(list)
    for i in range(Community_Iters):
        for index, row in Overlap_df.iterrows():
            Community_means = np.array([Overlap_df.loc[index, Coms[i]].mean() for i in Coms.index])
            Community_means[np.isnan(Community_means)] = 0
            if(Community_means.max() >= Cutoff): # get rid of combos less than our cutoff
                Community_df.loc[Community_df[Projection] == index, 'Community'] = np.argmax(Community_means)
            else:
                Community_df.loc[Community_df[Projection] == index, 'Community'] = Community_df['Community'].max() + 1
            Coms = Community_df.groupby('Community')[Projection].apply(list)

    Community_df = Community_df.sort_values(by = ['Community']).reset_index(drop = True)
    Overlap_df = Overlap_df.loc[Community_df[Projection], Community_df[Projection]]

    Community_Mapping = {i:list(Coms.index).index(i) for i in list(Coms.index)}
    Community_df['Community'] = Community_df['Community'].map(Community_Mapping)
    Communities = {row[Projection]:row['Community'] for index, row in Community_df.iterrows()}
    Community_df = Community_df.set_index(Projection).set_index('Community', append = True).sort_index(level = 1).reset_index(level = 1)

    nx.set_node_attributes(G, Communities, 'Community')
    print('Modularity: {}'.format(community.modularity(Communities, G, weight = 'weight')))
    G1 = hv.Graph.from_networkx(G, nx.spring_layout, iterations = 50).options(width = 500, height = 500, color_index = 'Community', cmap = 'tab10',
                                                                                edge_color_index = 'weight', edge_cmap = 'Greys', show_frame = False,
                                                                                xaxis = None, yaxis = None)

    plt.figure(figsize = (12, 12))
    cm = plt.cm.get_cmap('coolwarm')
    matplotlib.rcParams.update({'font.size': 6})
    HeatMap = plt.pcolor(Overlap_df.fillna(0), cmap = cm)
    plt.yticks(np.arange(0.5, len(Overlap_df.index), 1), Overlap_df.index)
    plt.xticks(np.arange(0.5, len(Overlap_df.columns), 1), Overlap_df.columns, rotation = 90)
    plt.colorbar(HeatMap)
    plt.show()

    return Community_df, Overlap_df, G1

def SankeyNodeShifts(Community_Predf, Community_Postdf):
    """Create Sankey diagrams illustrating shifts in community belonging from pre to post.

    Keyword arguments:
    Community_Predf -- dataframe of pretest community belonging by item from either FindCommunities or IterativeCommunityFinding
    Community_Postdf -- dataframe of pretest community belonging by item from either FindCommunities or IterativeCommunityFinding
    """

    Source = []
    Target = []
    Value = []
    Community_Predf['Item'] = Community_Predf.index
    Community_Postdf['Item'] = Community_Postdf.index
    Community_Postdf['Community'] = Community_Postdf['Community'] + Community_Predf['Community'].max() + 1
    for c_pre in range(Community_Predf['Community'].max() + 1):
        for c_post in range(Community_Postdf['Community'].min(), Community_Postdf['Community'].max() + 1):
            Link = sum(Community_Postdf.loc[Community_Postdf['Community'] == c_post, 'Item'].isin(Community_Predf.loc[Community_Predf['Community']  == c_pre, 'Item']))
            Source.append(c_pre)
            Target.append(c_post)
            Value.append(Link)

    data = dict(
        type='sankey',
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(
            color = "black",
            width = 0.5
          ),
          label = ["Pretest community " + str(i) for i in range(Community_Predf['Community'].max() + 1)] + ["Posttest community " + str(i) for i in range(Community_Postdf['Community'].max() + 1)],
          color = ["blue" for i in range(Community_Predf['Community'].max() + 1)] + ["red" for i in range(Community_Postdf['Community'].max() + 1)]
        ),
        link = dict(
          source = Source,
          target = Target,
          value = Value
      ))

    layout =  dict(
        title = "Response choice community Shifts",
        font = dict(
          size = 20
        )
    )

    fig = dict(data=[data], layout=layout)
    py.plot(fig, validate = False)

def SankeyItemTrees(Com_dfs = [], Labels = [], Projection = 'Item'):
    """Create Sankey diagrams illustrating shifts in community belonging with variable number of timepoints.

    Keyword arguments:
    Coms_dfs -- list of dataframes of community belonging by item from either FindCommunities or IterativeCommunityFinding
    Labels -- list of labels to associate with each community dataframe
    Projection -- either Item or Students, which level the networks have been projected
    """

    assert(len(Com_dfs) == len(Labels))

    Colors = cl.scales[str(max(len(Com_dfs), 3))]['div']['RdYlBu']

    Source = []
    Target = []
    Value = []

    for i, df in enumerate(Com_dfs):
        if(i == len(Com_dfs) - 1):
            break
        Com_dfs[i + 1].loc[:, 'Community'] = Com_dfs[i + 1].loc[:, 'Community'] + Com_dfs[i].loc[:, 'Community'].max() + 1
        for c_pre in range(Com_dfs[i].loc[:, 'Community'].max() + 1):
            for c_post in range(Com_dfs[i + 1].loc[:, 'Community'].min(), Com_dfs[i + 1].loc[:, 'Community'].max() + 1):
                Link = sum(Com_dfs[i + 1].loc[Com_dfs[i + 1].loc[:, 'Community'] == c_post, Projection].isin(Com_dfs[i].loc[Com_dfs[i].loc[:, 'Community']  == c_pre, Projection]))
                Source.append(c_pre)
                Target.append(c_post)
                Value.append(Link)

    data = dict(
        type='sankey',
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(
            color = "black",
            width = 0.5
          ),
          label = [Labels[i] + '_' + str(c) for i in range(len(Com_dfs)) for c in range(Com_dfs[i].loc[:, 'Community'].max() - Com_dfs[i].loc[:, 'Community'].min()  + 1)],
          color = [Colors[i] for i in range(len(Com_dfs)) for c in range(Com_dfs[i].loc[:, 'Community'].max() - Com_dfs[i].loc[:, 'Community'].min() + 1)]
        ),
        link = dict(
          source = Source,
          target = Target,
          value = Value
      ))

    layout =  dict(
        title = "Item-Community Shifts",
        font = dict(
          size = 10
        )
    )

    fig = dict(data=[data], layout=layout)
    py.plot(fig, validate = False)


def StudentProfiles(Student_df, Community_df = None, Survey = 'PRE', Compute = True, Iterate = False, **kwargs):

    if(Survey == 'PRE'):
        appendix = '_x'
    elif(Survey == 'POST'):
        appendix = '_y'

    if Compute:

        if Iterate:

            Community_df, O1_df, G1 = IterativeCommunityFinding(Student_df, Survey = Survey, Projection = 'Item', **kwargs)

        else:

            Community_df, G1, D = FindCommunities(Student_df, Survey = Survey, Projection = 'Item', **kwargs)

        Student_df, G2 = FindCommunities(Student_df, Survey = Survey, Projection = 'Students', **kwargs)

    Coms_array = Community_df.reset_index().rename(columns = {'index':'Item'}).groupby('Community')['Item'].apply(list).values

    for i, com in enumerate(Coms_array):
        com_arr = [col + appendix for col in com]
        Student_df.loc[:, 'Item_Com_' + str(i)] = Student_df.loc[:, com_arr].sum(axis = 1, numeric_only = False)

    Student_df.loc[:, 'Item_Com_0':] = Student_df.loc[:, 'Item_Com_0':].divide(Student_df.loc[:, 'Item_Com_0':].sum(axis = 1), axis = 0)

    return Student_df, Community_df, G1
