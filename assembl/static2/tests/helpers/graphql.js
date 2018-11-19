/* Helpers for tests involving graphql/apollo */
import { ApolloClient } from 'react-apollo';
import { mockNetworkInterface } from 'react-apollo/test-utils';

import CreateResource from '../../js/app/graphql/mutations/createResource.graphql';
import DeleteResource from '../../js/app/graphql/mutations/deleteResource.graphql';
import UpdateResource from '../../js/app/graphql/mutations/updateResource.graphql';
import UpdateResourcesCenter from '../../js/app/graphql/mutations/updateResourcesCenter.graphql';
import ResourcesCenterPage from '../../js/app/graphql/ResourcesCenterPage.graphql';

const MockedResponses = [
  {
    request: {
      query: ResourcesCenterPage,
      variables: {
        lang: 'en'
      }
    },
    result: {
      data: {
        resourcesCenter: {
          title: 'My RC',
          titleEntries: [],
          headerImage: null
        }
      }
    }
  },
  {
    request: {
      query: UpdateResourcesCenter,
      variables: {
        titleEntries: [{ localeCode: 'en', value: 'Resources center' }, { localeCode: 'fr', value: 'Centre de ressources' }],
        headerImage: null
      }
    },
    result: {
      data: {
        updateResourcesCenter: {
          resourcesCenter: {
            titleEntries: [{ localeCode: 'en', value: 'Resources center' }, { localeCode: 'fr', value: 'Centre de ressources' }],
            headerImage: null
          }
        }
      }
    }
  },
  {
    request: {
      query: DeleteResource,
      variables: {
        resourceId: 'resource-to-delete'
      }
    },
    result: {
      data: {
        deleteResource: {
          success: true
        }
      }
    }
  },
  {
    request: {
      query: CreateResource,
      variables: {
        lang: 'en',
        doc: null,
        embedCode: '',
        image: null,
        textEntries: [],
        titleEntries: [
          {
            localeCode: 'en',
            value: 'My new resource'
          },
          {
            localeCode: 'fr',
            value: 'Ma nouvelle ressource'
          }
        ],
        order: 1
      }
    },
    result: {
      data: {
        createResource: {
          resource: {
            doc: null,
            id: 'UTIESRN83X',
            image: null,
            title: 'My new resource',
            titleEntries: [
              {
                localeCode: 'en',
                value: 'My new resource'
              },
              {
                localeCode: 'fr',
                value: 'Ma nouvelle ressource'
              }
            ],
            text: '',
            textEntries: [],
            embedCode: '',
            order: 1.0
          }
        }
      }
    }
  },
  {
    request: {
      query: UpdateResource,
      variables: {
        id: 'resource-to-update',
        lang: 'en',
        doc: null,
        embedCode: '<iframe></iframe>',
        image: null,
        textEntries: [
          {
            localeCode: 'en',
            value: '<p>After update</p>'
          },
          {
            localeCode: 'fr',
            value: '<p>Après mise à jour</p>'
          }
        ],
        titleEntries: [
          {
            localeCode: 'en',
            value: 'Resource to update'
          },
          {
            localeCode: 'fr',
            value: 'Ressource à mettre à jour'
          }
        ],
        order: null
      }
    },
    result: {
      data: {
        updateResource: {
          resource: {
            doc: null,
            embedCode: '<iframe></iframe>',
            id: 'resource-to-update',
            image: null,
            order: 2.0,
            text: '<p>After update</p>',
            textEntries: [
              {
                localeCode: 'fr',
                value: '<p>Après mise à jour</p>'
              },
              {
                localeCode: 'en',
                value: '<p>After update</p>'
              }
            ],
            title: 'Resource to update',
            titleEntries: [
              {
                localeCode: 'en',
                value: 'Resource to update'
              },
              {
                localeCode: 'fr',
                value: 'Ressource à mettre à jour'
              }
            ]
          }
        }
      }
    }
  }
];

const mockedNetworkInterface = mockNetworkInterface(...MockedResponses);

export const client = new ApolloClient({
  addTypename: false,
  networkInterface: mockedNetworkInterface
});